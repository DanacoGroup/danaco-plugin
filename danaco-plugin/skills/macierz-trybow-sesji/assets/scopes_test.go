package shared

import "testing"

// Macierz widoczności jest generowana, więc nie może być jedynym sędzią samej siebie.
// Ten test pilnuje własności, które muszą zachodzić niezależnie od treści kontraktu.

func TestEveryModeHasScope(t *testing.T) {
	if len(ModeScopes) == 0 {
		t.Fatal("macierz zakresów jest pusta - uruchom modes_tool.py gen")
	}
	for id := range Modes {
		if _, ok := ModeScopes[id]; !ok {
			t.Errorf("tryb %s nie ma wpisu w macierzy zakresów", id)
		}
	}
	for id := range ModeScopes {
		if _, ok := Modes[id]; !ok {
			t.Errorf("macierz zakresów zna tryb %s, którego nie ma w rejestrze", id)
		}
	}
}

func TestEveryModeReadsAndWritesItself(t *testing.T) {
	for id := range ModeScopes {
		if !CanRead(id, id) {
			t.Errorf("tryb %s nie czyta własnego stanu - to zawsze jest błąd macierzy", id)
		}
		if !CanWrite(id, id) {
			t.Errorf("tryb %s nie pisze do własnej przestrzeni", id)
		}
	}
}

func TestIsolatedModeIsNotReadByOthers(t *testing.T) {
	for id, info := range Modes {
		if info.Isolation != "isolated" {
			continue
		}
		for other := range ModeScopes {
			if other != id && CanRead(other, id) {
				t.Errorf("tryb %s czyta z izolowanego %s", other, id)
			}
		}
	}
}

func TestNonSharedModeWritesOnlyItself(t *testing.T) {
	for id, info := range Modes {
		if info.Isolation == "shared" {
			continue
		}
		for other := range ModeScopes {
			if other != id && CanWrite(id, other) {
				t.Errorf("tryb %s (%s) pisze do %s poza własną przestrzenią", id, info.Isolation, other)
			}
		}
	}
}

func TestUnknownModeHasNoRights(t *testing.T) {
	obcy := ModeID("nie.ma")
	for id := range ModeScopes {
		if CanRead(obcy, id) || CanWrite(obcy, id) || CanRead(id, obcy) || CanWrite(id, obcy) {
			t.Errorf("tryb spoza kontraktu ma prawa wobec %s", id)
		}
	}
	if AIChannelAllowed(obcy, 0) {
		t.Error("tryb spoza kontraktu dopuszcza tor AI")
	}
}

func TestAIChannelNotWeakerThanMode(t *testing.T) {
	strength := map[string]int{"shared": 0, "hybrid": 1, "isolated": 2}
	for id, scope := range ModeScopes {
		if !scope.AIAllowed {
			continue
		}
		info := Modes[id]
		if strength[string(scope.AIIsolation)] < strength[info.Isolation] {
			t.Errorf("tryb %s: tor AI (%s) słabiej izolowany niż tryb (%s)",
				id, scope.AIIsolation, info.Isolation)
		}
		if scope.AIMaxChannels < 1 || scope.AIMaxChannels > 4 {
			t.Errorf("tryb %s: maxChannels poza zakresem 1-4: %d", id, scope.AIMaxChannels)
		}
	}
}

func TestAIChannelAllowedRespectsLimit(t *testing.T) {
	for id, scope := range ModeScopes {
		if !scope.AIAllowed {
			if AIChannelAllowed(id, 0) {
				t.Errorf("tryb %s nie dopuszcza AI, a AIChannelAllowed zwraca true", id)
			}
			continue
		}
		if !AIChannelAllowed(id, scope.AIMaxChannels-1) {
			t.Errorf("tryb %s: ostatni dopuszczalny tor został odrzucony", id)
		}
		if AIChannelAllowed(id, scope.AIMaxChannels) {
			t.Errorf("tryb %s: przekroczenie limitu torów zostało przepuszczone", id)
		}
	}
}
