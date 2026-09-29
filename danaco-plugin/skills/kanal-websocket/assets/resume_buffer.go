package transport

import (
	"errors"
	"sync"

	"danacoconsole/shared"
)

// ErrResumeGap oznacza, że klient prosi o numer starszy niż najstarszy w buforze.
// Odpowiedzią jest pełne przeładowanie stanu, nie ciche wznowienie od czegokolwiek -
// dziura w strumieniu zdarzeń jest gorsza od przeładowania, bo nie widać jej od razu.
var ErrResumeGap = errors.New(string(shared.ErrResumeGap))

// ErrResumeAhead oznacza, że klient twierdzi, iż odebrał numer, którego rdzeń jeszcze nie nadał.
// To błąd protokołu (inna sesja, restart rdzenia bez zmiany identyfikatora sesji), nie stan
// przejściowy - klient ma przeładować stan, a nie czekać na koperty, które nie nadejdą.
var ErrResumeAhead = errors.New(string(shared.ErrResumeGap) + ": numer spoza strumienia")

// ResumeBuffer trzyma ostatnie koperty wysłane w sesji, żeby po zerwaniu połączenia
// klient mógł wznowić od miejsca, w którym przestał odbierać.
//
// W aplikacji desktopowej zerwane połączenie jest stanem normalnym: uśpiony laptop,
// restart rdzenia, przełączenie sieci. Bufor zamienia to z utraty pracy w chwilową przerwę.
// Bufor jest na sesję, nie na połączenie - bufor związany z połączeniem znikałby
// dokładnie wtedy, gdy jest potrzebny.
type ResumeBuffer struct {
	mu    sync.Mutex
	buf   []shared.Envelope
	first uint64 // numer sekwencyjny pierwszej koperty w buforze
	next  uint64 // numer, który dostanie następna koperta
	limit int
}

// NewResumeBuffer tworzy bufor o zadanej pojemności.
// Pojemność to kompromis: za mała oznacza częste pełne przeładowania,
// za duża trzyma w pamięci zdarzenia, po które nikt nie wróci.
func NewResumeBuffer(limit int) *ResumeBuffer {
	if limit < 1 {
		limit = 1
	}
	return &ResumeBuffer{buf: make([]shared.Envelope, 0, limit), first: 1, next: 1, limit: limit}
}

// Append nadaje kopercie kolejny numer sekwencyjny i zapamiętuje ją.
// Numer jest wspólny dla całej sesji, także dla zdarzeń z różnych torów AI -
// dzięki temu przeplot jest odtwarzalny przy każdym wznowieniu.
func (b *ResumeBuffer) Append(env shared.Envelope) shared.Envelope {
	b.mu.Lock()
	defer b.mu.Unlock()
	env.Seq = b.next
	b.next++
	b.buf = append(b.buf, env)
	if len(b.buf) > b.limit {
		overflow := len(b.buf) - b.limit
		// Przesunięcie w miejscu utrzymuje jedną tablicę o pojemności limit;
		// przesuwanie wycinka do przodu wymuszałoby okresowe realokacje i kopie.
		b.buf = append(b.buf[:0], b.buf[overflow:]...)
		b.first += uint64(overflow)
	}
	return env
}

// Since zwraca koperty o numerach większych niż seq - ogon strumienia od seq+1.
// Zwraca ErrResumeGap, gdy żądany numer wypadł już z bufora, i ErrResumeAhead,
// gdy klient podaje numer większy niż ostatni nadany.
func (b *ResumeBuffer) Since(seq uint64) ([]shared.Envelope, error) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if seq+1 < b.first {
		return nil, ErrResumeGap
	}
	if seq+1 > b.next {
		return nil, ErrResumeAhead
	}
	if seq+1 == b.next {
		return nil, nil
	}
	from := int(seq + 1 - b.first)
	out := make([]shared.Envelope, b.next-seq-1)
	copy(out, b.buf[from:])
	return out, nil
}

// Next zwraca numer, który dostanie następna koperta.
func (b *ResumeBuffer) Next() uint64 {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.next
}

// Len zwraca liczbę kopert trzymanych obecnie w buforze (nie więcej niż pojemność).
func (b *ResumeBuffer) Len() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	return len(b.buf)
}
