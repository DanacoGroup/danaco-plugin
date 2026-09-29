// Pakiet orchestration zawiera pętlę wykonawczą czterech modeli AI jako przepływ Temporal.
//
// Temporal jest tu wybrany nie dla rozproszenia, tylko dla trwałości: pętla ma pracować
// dobami bez człowieka, a restart rdzenia, awaria zasilania czy wdrożenie nowej wersji
// nie mogą oznaczać zaczynania od początku. Historia przepływu jest jednocześnie
// dziennikiem audytowym - odpowiada na pytanie, który model co zrobił i ile to kosztowało.
package orchestration

import (
	"errors"
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

// StopSignal to nazwa sygnału wyłącznika awaryjnego.
// Pętla bez wyłącznika, która działa bez człowieka, jest pętlą, której nie da się zatrzymać.
const StopSignal = "zatrzymaj"

// RoundsPerHistory mówi, co ile rund przepływ zaczyna nową historię (ContinueAsNew).
// Historia rośnie z każdą rundą; pętla działająca dobami bez tego przewraca się o własny rozmiar.
const RoundsPerHistory = 50

// Spec opisuje jedno uruchomienie pętli. Odpowiada definicji z workflows/*.json,
// sprawdzanej przez tools/workflow_tool.py przed startem. Te same progi są sprawdzane
// tu ponownie, bo przepływ może zostać uruchomiony z pominięciem walidatora.
type Spec struct {
	ID              string
	Goal            string
	Mode            string
	TotalTokens     int64
	WallClockHours  int
	MaxRetries      int
	NoProgressLimit int
}

// Validate odrzuca specyfikację, w której brakuje któregoś zabezpieczenia.
// Brakujący próg nie jest "brakiem ograniczenia" - jest progiem zero, przy którym
// pętla kończy się natychmiast albo nigdy, zależnie od warunku.
func (s Spec) Validate() error {
	var problemy []string
	if s.ID == "" {
		problemy = append(problemy, "brak identyfikatora")
	}
	if s.TotalTokens <= 0 {
		problemy = append(problemy, "TotalTokens musi być dodatnie")
	}
	if s.WallClockHours <= 0 {
		problemy = append(problemy, "WallClockHours musi być dodatnie")
	}
	if s.MaxRetries < 1 {
		problemy = append(problemy, "MaxRetries musi wynosić co najmniej 1")
	}
	if s.NoProgressLimit < 1 {
		problemy = append(problemy, "NoProgressLimit musi wynosić co najmniej 1")
	}
	if len(problemy) > 0 {
		return fmt.Errorf("specyfikacja pętli %q: %v", s.ID, problemy)
	}
	return nil
}

// State przenosi się między kolejnymi wcieleniami przepływu przy ContinueAsNew.
type State struct {
	SpentTokens      int64
	Rounds           int
	NoProgressRounds int
	StartUnixNano    int64
	// Deferred to zadania, które wyczerpały MaxRetries. Nie znikają - koordynator
	// widzi je przy planowaniu, a licznik braku postępu rośnie.
	Deferred []Task
}

// Task to jednostka pracy w kolejce.
type Task struct {
	ID          string
	Description string
	Role        string
	Attempt     int
}

// StepResult wraca z aktywności wykonywanej przez model.
type StepResult struct {
	Tasks       []Task
	SpentTokens int64
	Progress    bool
	Reason      string
}

// ReviewResult wraca z bramki kontroli.
type ReviewResult struct {
	Accepted    bool
	Notes       string
	SpentTokens int64
}

// AcceptanceResult wraca z bramki akceptacji - to jedyne miejsce, które kończy pętlę sukcesem.
type AcceptanceResult struct {
	Passed   bool
	Failures []string
}

// LoopResult to rezultat całej pętli.
type LoopResult struct {
	Completed   bool
	Reason      string
	Rounds      int
	SpentTokens int64
}

// ErrInvalidSpec oznacza specyfikację odrzuconą przez Validate.
var ErrInvalidSpec = errors.New("niepoprawna specyfikacja pętli")

// Aktywności wykonywane poza przepływem. Każda woła jeden model albo jedną bramkę.
// Deklarujemy je jako zmienne, żeby przepływ dało się testować z atrapami.
var (
	ActPlan           = "Zaplanuj"
	ActBuild          = "Wykonaj"
	ActReview         = "Skontroluj"
	ActAcceptanceGate = "BramkaAkceptacji"
	ActEscalate       = "Eskaluj"
)

// ExecutionLoop prowadzi pracę czterech modeli aż do przejścia bramki akceptacji,
// wyczerpania budżetu, przekroczenia czasu albo braku postępu.
//
// Wszystkie cztery warunki końca są tu jawne. Pętla, która kończy się wyłącznie
// na "koordynator uznał, że gotowe", nie ma warunku końca - ma opinię.
func ExecutionLoop(ctx workflow.Context, spec Spec, state State) (LoopResult, error) {
	if err := spec.Validate(); err != nil {
		return LoopResult{}, fmt.Errorf("%w: %v", ErrInvalidSpec, err)
	}

	opts := workflow.ActivityOptions{
		StartToCloseTimeout: time.Hour,
		HeartbeatTimeout:    5 * time.Minute,
		RetryPolicy: &temporal.RetryPolicy{
			MaximumAttempts: int32(spec.MaxRetries),
		},
	}
	ctx = workflow.WithActivityOptions(ctx, opts)
	logger := workflow.GetLogger(ctx)

	if state.StartUnixNano == 0 {
		state.StartUnixNano = workflow.Now(ctx).UnixNano()
	}
	deadline := time.Unix(0, state.StartUnixNano).Add(time.Duration(spec.WallClockHours) * time.Hour)

	// Wyłącznik awaryjny. Sygnał jest sprawdzany na początku każdej rundy i po każdym
	// zadaniu, więc zatrzymuje po bieżącym zadaniu, nie w jego środku.
	stopChan := workflow.GetSignalChannel(ctx, StopSignal)
	stopped := false
	workflow.Go(ctx, func(gctx workflow.Context) {
		var reason string
		stopChan.Receive(gctx, &reason)
		stopped = true
		workflow.GetLogger(gctx).Info("pętla zatrzymana sygnałem", "reason", reason)
	})

	wynik := func(reason string, completed bool) LoopResult {
		return LoopResult{Completed: completed, Reason: reason, Rounds: state.Rounds, SpentTokens: state.SpentTokens}
	}

	for {
		switch {
		case stopped:
			return wynik("zatrzymana sygnałem", false), nil
		case state.SpentTokens >= spec.TotalTokens:
			return wynik("wyczerpany budżet", false), nil
		case workflow.Now(ctx).After(deadline):
			return wynik("przekroczony czas", false), nil
		case state.NoProgressRounds >= spec.NoProgressLimit:
			if err := workflow.ExecuteActivity(ctx, ActEscalate, spec, state).Get(ctx, nil); err != nil {
				logger.Error("eskalacja nie powiodła się", "err", err)
			}
			return wynik("brak postępu", false), nil
		}

		state.Rounds++

		var plan StepResult
		if err := workflow.ExecuteActivity(ctx, ActPlan, spec, state).Get(ctx, &plan); err != nil {
			return LoopResult{}, err
		}
		state.SpentTokens += plan.SpentTokens

		if len(plan.Tasks) == 0 {
			// Koordynator nie ma już co zlecić - czas sprawdzić bramkę akceptacji.
			var acceptance AcceptanceResult
			if err := workflow.ExecuteActivity(ctx, ActAcceptanceGate, spec).Get(ctx, &acceptance); err != nil {
				return LoopResult{}, err
			}
			if acceptance.Passed {
				return wynik("bramka akceptacji przeszła", true), nil
			}
			// Bramka odrzuciła - to jest postęp informacyjny, ale nie postęp w pracy.
			logger.Info("bramka akceptacji odrzuciła", "niepowodzenia", acceptance.Failures)
			state.NoProgressRounds++
			continue
		}

		progressThisRound := false
		for _, task := range plan.Tasks {
			if stopped {
				// Zatrzymanie po bieżącym zadaniu, nie w jego środku: przerwanie w połowie
				// zapisu zostawiłoby przestrzeń roboczą w stanie pośrednim.
				break
			}
			if task.Attempt > spec.MaxRetries {
				state.Deferred = append(state.Deferred, task)
				logger.Info("zadanie odłożone po wyczerpaniu prób", "task", task.ID)
				continue
			}

			var build StepResult
			if err := workflow.ExecuteActivity(ctx, ActBuild, task).Get(ctx, &build); err != nil {
				return LoopResult{}, err
			}
			state.SpentTokens += build.SpentTokens

			// Kontrola dostaje sam wynik, bez uzasadnienia wykonawcy - inaczej ocenia
			// rozumowanie zamiast rezultatu i przyjmuje znacznie chętniej.
			var review ReviewResult
			if err := workflow.ExecuteActivity(ctx, ActReview, task).Get(ctx, &review); err != nil {
				return LoopResult{}, err
			}
			state.SpentTokens += review.SpentTokens

			if review.Accepted {
				progressThisRound = true
			} else {
				logger.Info("kontrola odrzuciła zadanie", "task", task.ID, "uwagi", review.Notes)
			}
		}

		if progressThisRound {
			state.NoProgressRounds = 0
		} else {
			state.NoProgressRounds++
		}

		// Historia przepływu rośnie z każdą rundą. ContinueAsNew zaczyna nową historię
		// z tym samym stanem. Sygnał, który nadszedł tuż przed przejściem, nie może przepaść:
		// kanał jest opróżniany, a zatrzymanie kończy pętlę zamiast przenosić ją dalej.
		if state.Rounds%RoundsPerHistory == 0 {
			var reason string
			for stopChan.ReceiveAsync(&reason) {
				stopped = true
			}
			if stopped {
				return wynik("zatrzymana sygnałem", false), nil
			}
			return LoopResult{}, workflow.NewContinueAsNewError(ctx, ExecutionLoop, spec, state)
		}
	}
}
