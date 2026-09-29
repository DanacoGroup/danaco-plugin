package shared

import "testing"

// Generator sam wytwarza poniższe struktury, więc nie może być jedynym ich sędzią.
// Ten test sprawdza spójność wygenerowanego rejestru i łapie regresje samego generatora.

func TestEveryModeIsComplete(t *testing.T) {
	if len(Modes) == 0 {
		t.Fatal("rejestr trybów jest pusty - kontrakt nie zawiera sekcji modes")
	}
	for id, info := range Modes {
		if info.ID != id {
			t.Errorf("tryb %s: pole ID (%s) nie zgadza się z kluczem mapy", id, info.ID)
		}
		if info.Environment == "" || info.Module == "" {
			t.Errorf("tryb %s: brak środowiska albo modułu", id)
		}
		if info.Isolation == "" {
			t.Errorf("tryb %s: brak poziomu izolacji - każdy tryb musi go deklarować jawnie", id)
		}
		if _, ok := LookupMode(id); !ok {
			t.Errorf("tryb %s: LookupMode go nie odnajduje", id)
		}
	}
}

func TestEveryErrorCodeHasMessage(t *testing.T) {
	if len(ErrorMessages) == 0 {
		t.Fatal("mapa ErrorMessages jest pusta - kontrakt nie deklaruje kodów błędów")
	}
	for code, msg := range ErrorMessages {
		if msg == "" {
			t.Errorf("kod błędu %s nie ma treści komunikatu", code)
		}
	}
}

func TestEveryMessageHasDirection(t *testing.T) {
	if len(MessageDirection) == 0 {
		t.Skip("kontrakt nie deklaruje komunikatów")
	}
	for typ, dir := range MessageDirection {
		switch dir {
		case "clientToServer", "serverToClient", "bidirectional":
		default:
			t.Errorf("komunikat %s ma nieznany kierunek %q", typ, dir)
		}
	}
}

func TestNewPayloadMatchesRegistry(t *testing.T) {
	// Każdy komunikat z rejestru albo dostaje pustą strukturę ładunku, albo jawnie jej nie ma;
	// typ spoza kontraktu nigdy nie dostaje struktury.
	for typ := range MessageDirection {
		payload, ok := NewPayload(typ)
		if ok && payload == nil {
			t.Errorf("komunikat %s: NewPayload zgłasza ładunek, ale zwraca nil", typ)
		}
	}
	if _, ok := NewPayload(MessageType("nie.ma.takiego")); ok {
		t.Error("NewPayload zwrócił strukturę dla komunikatu spoza kontraktu")
	}
}

func TestMessageResponseIsClientToServer(t *testing.T) {
	for req, resp := range MessageResponse {
		if MessageDirection[req] == "serverToClient" {
			t.Errorf("komunikat %s ma response, a jest wysyłany przez rdzeń", req)
		}
		if _, ok := MessageDirection[resp]; !ok {
			t.Errorf("komunikat %s wskazuje odpowiedź %s spoza rejestru", req, resp)
		}
	}
}

func TestContractHashIsPresent(t *testing.T) {
	if ContractHash == "" || ContractVersion == "" {
		t.Fatal("brak wersji albo skrótu kontraktu - uścisk dłoni nie ma czego porównywać")
	}
}
