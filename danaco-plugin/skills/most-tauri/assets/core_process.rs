//! Nadzór nad rdzeniem Go uruchamianym jako proces poboczny powłoki Tauri.
//!
//! Moduł celowo nie zależy od API Tauri - dzięki temu da się go skompilować i przetestować
//! bez całego projektu powłoki, a to jest warstwa, w której błąd kosztuje najwięcej:
//! proces-sierota po zamknięciu aplikacji blokuje port przy następnym starcie.
//!
//! Umowa z rdzeniem:
//! - rdzeń dostaje `--data-dir <katalog>` i wypisuje na stdout jedną linię `PORT=<numer>`,
//! - dziennik rdzenia idzie na stderr (stdout jest kanałem uzgodnienia),
//! - zamknięcie stdin przez powłokę jest prośbą o łagodne zakończenie; rdzeń, który
//!   nie zdąży w wyznaczonym czasie, jest zabijany.

use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::mpsc::{self, RecvTimeoutError};
use std::thread;
use std::time::{Duration, Instant};

/// Błąd uruchomienia rdzenia.
#[derive(Debug)]
pub enum CoreError {
    /// Nie udało się uruchomić procesu.
    Spawn(std::io::Error),
    /// Rdzeń nie zgłosił portu w wyznaczonym czasie (albo zakończył się, zanim go zgłosił).
    HandshakeTimeout,
    /// Rdzeń zgłosił coś, czego nie da się odczytać jako numer portu.
    BadHandshake(String),
}

impl std::fmt::Display for CoreError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CoreError::Spawn(e) => write!(f, "nie udało się uruchomić rdzenia: {e}"),
            CoreError::HandshakeTimeout => write!(f, "rdzeń nie zgłosił portu w wyznaczonym czasie"),
            CoreError::BadHandshake(s) => write!(f, "nieczytelny uścisk dłoni rdzenia: {s}"),
        }
    }
}

impl std::error::Error for CoreError {}

/// Uchwyt do działającego rdzenia.
pub struct CoreProcess {
    child: Child,
    stdin: Option<ChildStdin>,
    port: u16,
}

impl CoreProcess {
    /// Uruchamia rdzeń i czeka, aż zgłosi port.
    ///
    /// Odczyt stdout idzie w osobnym wątku, a czekanie ma twardy limit czasu. Rdzeń, który
    /// milczy (zawiesił się przy starcie, czeka na zajęty zasób), nie może zablokować powłoki
    /// na zawsze - a blokujący `read_line` w wątku okna robiłby dokładnie to.
    ///
    /// Uzgadnianie portu jest lepsze od stałego numeru: instalacja on-premise potrafi mieć
    /// zajęty każdy port wybrany z góry, a wtedy aplikacja nie wstaje i nie wiadomo dlaczego.
    pub fn spawn(exe: &Path, data_dir: &Path, timeout: Duration) -> Result<Self, CoreError> {
        let mut child = Command::new(exe)
            .arg("--data-dir")
            .arg(data_dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(CoreError::Spawn)?;

        let stdin = child.stdin.take();
        let stdout = child.stdout.take().expect("stdout został ustawiony na piped");

        // Wątek czyta linie i przekazuje je kanałem; kończy się razem z zamknięciem stdout.
        let (tx, rx) = mpsc::channel::<std::io::Result<String>>();
        thread::spawn(move || {
            let mut reader = BufReader::new(stdout);
            loop {
                let mut line = String::new();
                match reader.read_line(&mut line) {
                    Ok(0) => break,
                    Ok(_) => {
                        if tx.send(Ok(line)).is_err() {
                            break;
                        }
                    }
                    Err(e) => {
                        let _ = tx.send(Err(e));
                        break;
                    }
                }
            }
        });

        let start = Instant::now();
        loop {
            let remaining = timeout.saturating_sub(start.elapsed());
            if remaining.is_zero() {
                Self::kill_quietly(&mut child);
                return Err(CoreError::HandshakeTimeout);
            }
            match rx.recv_timeout(remaining) {
                Ok(Ok(line)) => {
                    if let Some(rest) = line.trim().strip_prefix("PORT=") {
                        return match rest.parse::<u16>() {
                            Ok(port) if port > 0 => Ok(CoreProcess { child, stdin, port }),
                            _ => {
                                Self::kill_quietly(&mut child);
                                Err(CoreError::BadHandshake(line.trim().to_string()))
                            }
                        };
                    }
                    // Inne linie przed uzgodnieniem to zwykle dziennik rdzenia - pomijamy.
                }
                Ok(Err(e)) => {
                    Self::kill_quietly(&mut child);
                    return Err(CoreError::Spawn(e));
                }
                Err(RecvTimeoutError::Timeout) => {
                    Self::kill_quietly(&mut child);
                    return Err(CoreError::HandshakeTimeout);
                }
                Err(RecvTimeoutError::Disconnected) => {
                    // stdout zamknięty bez linii PORT= - rdzeń zakończył się przed uzgodnieniem.
                    Self::kill_quietly(&mut child);
                    return Err(CoreError::HandshakeTimeout);
                }
            }
        }
    }

    /// Port, na którym rdzeń słucha kanału WebSocket.
    pub fn port(&self) -> u16 {
        self.port
    }

    /// Mówi, czy proces nadal działa. Wołaj to z heartbeatu powłoki:
    /// rdzeń, który padł, objawia się inaczej niż rdzeń, który tylko nie odpowiada.
    pub fn is_alive(&mut self) -> bool {
        matches!(self.child.try_wait(), Ok(None))
    }

    /// Zamyka rdzeń łagodnie: zamyka jego stdin (rdzeń traktuje koniec stdin jako prośbę
    /// o domknięcie sesji i zapis stanu), czeka najwyżej `grace`, potem zabija.
    ///
    /// Samo zabicie oznacza utratę niezapisanego stanu sesji przy każdym zamknięciu okna;
    /// samo czekanie oznacza, że zawieszony rdzeń blokuje zamknięcie aplikacji.
    /// Zwraca `true`, gdy rdzeń zakończył się sam w wyznaczonym czasie.
    pub fn shutdown_graceful(&mut self, grace: Duration) -> bool {
        drop(self.stdin.take());
        let start = Instant::now();
        while start.elapsed() < grace {
            if !self.is_alive() {
                let _ = self.child.wait();
                return true;
            }
            thread::sleep(Duration::from_millis(25));
        }
        self.shutdown();
        false
    }

    /// Zabija rdzeń natychmiast i czeka na jego zakończenie. Wariant awaryjny.
    pub fn shutdown(&mut self) {
        drop(self.stdin.take());
        Self::kill_quietly(&mut self.child);
    }

    fn kill_quietly(child: &mut Child) {
        let _ = child.kill();
        let _ = child.wait();
    }
}

impl Drop for CoreProcess {
    /// Zamknięcie okna musi zabić rdzeń. Bez tego kolejny start aplikacji zastaje
    /// zajęty port i wygląda na awarię sieci, a jest to własny proces sprzed chwili.
    /// `Drop` działa także przy panice powłoki - dlatego to on chroni przed sierotą.
    fn drop(&mut self) {
        self.shutdown();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn missing_binary_yields_spawn_error() {
        let result = CoreProcess::spawn(
            Path::new("/nie/ma/takiego/programu"),
            Path::new("/tmp"),
            Duration::from_millis(200),
        );
        assert!(matches!(result, Err(CoreError::Spawn(_))));
    }

    /// Zapisuje skrypt udający rdzeń i uruchamia go. Zapis i uruchomienie są pod jednym
    /// zamkiem: proces potomny innego testu, rozwidlony między zapisem a wykonaniem, trzymałby
    /// deskryptor otwarty do zapisu i wykonanie kończyłoby się losowym "Text file busy".
    #[cfg(unix)]
    fn spawn_script(body: &str, timeout: Duration) -> Result<CoreProcess, CoreError> {
        use std::io::Write;
        use std::os::unix::fs::PermissionsExt;
        use std::sync::Mutex;
        static ZAMEK: Mutex<()> = Mutex::new(());
        let _straz = ZAMEK.lock().unwrap_or_else(|e| e.into_inner());
        let dir = std::env::temp_dir().join(format!("core_process_test_{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join(format!("core_{}.sh", body.len()));
        {
            let mut f = std::fs::File::create(&path).unwrap();
            writeln!(f, "#!/bin/sh\n{body}").unwrap();
        }
        std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o755)).unwrap();
        CoreProcess::spawn(&path, Path::new("/tmp"), timeout)
    }

    #[cfg(unix)]
    #[test]
    fn silent_program_hits_timeout_instead_of_blocking() {
        // Program, który nic nie wypisuje, nie może zablokować powłoki - limit czasu musi
        // zadziałać także wtedy, gdy stdout jest otwarty i nigdy nie przychodzi żadna linia.
        let start = Instant::now();
        let result = spawn_script("sleep 5", Duration::from_millis(300));
        assert!(matches!(result, Err(CoreError::HandshakeTimeout)));
        assert!(start.elapsed() < Duration::from_secs(3), "limit czasu nie zadziałał");
    }

    #[cfg(unix)]
    #[test]
    fn program_exiting_without_handshake_is_not_accepted() {
        let result = spawn_script("echo 'dziennik na stdout' ; exit 0", Duration::from_millis(500));
        assert!(matches!(result, Err(CoreError::HandshakeTimeout)));
    }

    #[cfg(unix)]
    #[test]
    fn garbage_port_is_rejected() {
        let result = spawn_script("echo PORT=abc; sleep 5", Duration::from_millis(500));
        assert!(matches!(result, Err(CoreError::BadHandshake(_))));
    }

    #[cfg(unix)]
    #[test]
    fn handshake_after_log_lines_is_accepted_and_graceful_shutdown_works() {
        // Rdzeń wypisuje najpierw dziennik, potem PORT=, a po zamknięciu stdin kończy się sam.
        let mut core = spawn_script("echo 'start rdzenia'; echo PORT=4321; cat >/dev/null; exit 0", Duration::from_secs(2))
            .expect("uzgodnienie");
        assert_eq!(core.port(), 4321);
        assert!(core.is_alive());
        assert!(core.shutdown_graceful(Duration::from_secs(2)), "rdzeń nie zakończył się po zamknięciu stdin");
        assert!(!core.is_alive());
    }

    #[cfg(unix)]
    #[test]
    fn hung_core_is_killed_after_grace() {
        let mut core = spawn_script("echo PORT=4322; trap '' TERM; sleep 30", Duration::from_secs(2))
            .expect("uzgodnienie");
        let start = Instant::now();
        assert!(!core.shutdown_graceful(Duration::from_millis(200)));
        assert!(!core.is_alive());
        assert!(start.elapsed() < Duration::from_secs(5));
    }
}
