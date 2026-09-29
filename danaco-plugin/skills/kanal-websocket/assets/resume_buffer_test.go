package transport

import (
	"errors"
	"sync"
	"testing"

	"danacoconsole/shared"
)

func testEnvelope(t shared.MessageType) shared.Envelope {
	return shared.Envelope{Type: t, Channel: "session"}
}

func TestSequenceIsContiguous(t *testing.T) {
	b := NewResumeBuffer(10)
	for i := uint64(1); i <= 5; i++ {
		got := b.Append(testEnvelope(shared.MsgSessionOpened))
		if got.Seq != i {
			t.Fatalf("koperta %d dostała numer %d", i, got.Seq)
		}
	}
	if b.Next() != 6 {
		t.Fatalf("następny numer to %d, oczekiwano 6", b.Next())
	}
}

func TestResumeReturnsTail(t *testing.T) {
	b := NewResumeBuffer(10)
	for i := 0; i < 5; i++ {
		b.Append(testEnvelope(shared.MsgSessionOpened))
	}
	tail, err := b.Since(2)
	if err != nil {
		t.Fatalf("nieoczekiwany błąd: %v", err)
	}
	if len(tail) != 3 {
		t.Fatalf("oczekiwano 3 kopert, dostano %d", len(tail))
	}
	if tail[0].Seq != 3 || tail[2].Seq != 5 {
		t.Fatalf("złe numery w ogonie: %d..%d", tail[0].Seq, tail[2].Seq)
	}
}

func TestResumeFromHeadIsEmpty(t *testing.T) {
	b := NewResumeBuffer(10)
	for i := 0; i < 3; i++ {
		b.Append(testEnvelope(shared.MsgSessionOpened))
	}
	tail, err := b.Since(3)
	if err != nil || len(tail) != 0 {
		t.Fatalf("oczekiwano pustego ogona bez błędu, jest %d kopert, błąd %v", len(tail), err)
	}
}

func TestTooOldSequenceReturnsGap(t *testing.T) {
	b := NewResumeBuffer(3)
	for i := 0; i < 10; i++ {
		b.Append(testEnvelope(shared.MsgSessionOpened))
	}
	// w buforze zostały numery 8, 9, 10
	if b.Len() != 3 {
		t.Fatalf("bufor o pojemności 3 trzyma %d kopert", b.Len())
	}
	if _, err := b.Since(2); !errors.Is(err, ErrResumeGap) {
		t.Fatalf("oczekiwano ErrResumeGap, dostano %v", err)
	}
	tail, err := b.Since(7)
	if err != nil || len(tail) != 3 || tail[0].Seq != 8 {
		t.Fatalf("wznowienie z granicy bufora zawiodło: %d kopert, błąd %v", len(tail), err)
	}
	tail, err = b.Since(8)
	if err != nil || len(tail) != 2 {
		t.Fatalf("wznowienie od 8 zawiodło: %d kopert, błąd %v", len(tail), err)
	}
}

func TestSequenceAheadOfStreamIsRejected(t *testing.T) {
	b := NewResumeBuffer(10)
	b.Append(testEnvelope(shared.MsgSessionOpened))
	// Klient twierdzi, że odebrał numer 5, a rdzeń nadał dopiero 1 - to nie jest pusty ogon,
	// tylko rozjazd (inna sesja, restart rdzenia), po którym trzeba przeładować stan.
	if _, err := b.Since(5); !errors.Is(err, ErrResumeAhead) {
		t.Fatalf("oczekiwano ErrResumeAhead, dostano %v", err)
	}
}

func TestConcurrentAppendKeepsSequence(t *testing.T) {
	b := NewResumeBuffer(1000)
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				b.Append(testEnvelope(shared.MsgAiDelta))
			}
		}()
	}
	wg.Wait()
	if b.Next() != 801 {
		t.Fatalf("po 800 dopisaniach następny numer to %d", b.Next())
	}
	tail, err := b.Since(0)
	if err != nil {
		t.Fatalf("nieoczekiwany błąd: %v", err)
	}
	seen := make(map[uint64]bool, len(tail))
	for _, e := range tail {
		if seen[e.Seq] {
			t.Fatalf("numer %d powtórzył się", e.Seq)
		}
		seen[e.Seq] = true
	}
	if len(seen) != 800 {
		t.Fatalf("oczekiwano 800 różnych numerów, jest %d", len(seen))
	}
}
