#!/usr/bin/env python3
"""Generator konfiguracji Tailwind CSS (tailwind_config_gen.py).

Tworzy `tailwind.config.ts` albo `.js` z motywem: kolory, czcionki, odstępy,
punkty łamania i zalecane wtyczki. Nazwa wtyczki jest sprawdzana wzorcem nazwy
pakietu npm, bo trafia do wygenerowanego `require(...)`.

Użycie:
    python3 tailwind_config_gen.py --framework nextjs
    python3 tailwind_config_gen.py --js --colors brand:#3b82f6
    python3 tailwind_config_gen.py --plugins --output client/tailwind.config.ts

Kody wyjścia: 0 powodzenie, 1 niepowodzenie (zła specyfikacja, błąd zapisu).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Dozwolona nazwa pakietu npm: opcjonalny @zakres/, nazwa, opcjonalna podścieżka.
# Bez cudzysłowów, nawiasów i średników - nazwa trafia do wygenerowanego
# `require(...)`, więc dowolny tekst byłby wstrzyknięciem kodu do konfiguracji.
_VALID_PLUGIN_NAME = re.compile(r'^(@[a-zA-Z0-9_-]+/)?[a-zA-Z0-9_-]+(/[a-zA-Z0-9_.-]+)*$')

PREFIKS_OSTRZEZENIA = "ostrzeżenie:"


class TailwindConfigGenerator:
    """Generowanie plików konfiguracyjnych Tailwind CSS."""

    def __init__(
        self,
        typescript: bool = True,
        framework: str = "react",
        output_path: Optional[Path] = None,
    ):
        """typescript: konfiguracja .ts (inaczej .js); framework: react, vue,
        svelte albo nextjs; output_path: plik wyjściowy (domyślnie wyliczany)."""
        self.typescript = typescript
        self.framework = framework
        self.output_path = output_path or self._default_output_path()
        self.config: Dict[str, Any] = self._base_config()

    def _default_output_path(self) -> Path:
        """Domyślna ścieżka pliku wyjściowego."""
        ext = "ts" if self.typescript else "js"
        return Path.cwd() / f"tailwind.config.{ext}"

    def _base_config(self) -> Dict[str, Any]:
        """Podstawowa struktura konfiguracji."""
        return {
            "darkMode": ["class"],
            "content": self._default_content_paths(),
            "theme": {
                "extend": {}
            },
            "plugins": []
        }

    def _default_content_paths(self) -> List[str]:
        """Domyślne ścieżki `content` dla wybranego frameworka."""
        paths = {
            "react": [
                "./src/**/*.{js,jsx,ts,tsx}",
                "./index.html",
            ],
            "vue": [
                "./src/**/*.{vue,js,ts,jsx,tsx}",
                "./index.html",
            ],
            "svelte": [
                "./src/**/*.{svelte,js,ts}",
                "./src/app.html",
            ],
            "nextjs": [
                "./app/**/*.{js,ts,jsx,tsx}",
                "./pages/**/*.{js,ts,jsx,tsx}",
                "./components/**/*.{js,ts,jsx,tsx}",
            ],
        }
        return paths.get(self.framework, paths["react"])

    def add_colors(self, colors: Dict[str, str]) -> None:
        """Kolory motywu: nazwa -> wartość szesnastkowa albo zmienna CSS."""
        if "colors" not in self.config["theme"]["extend"]:
            self.config["theme"]["extend"]["colors"] = {}

        self.config["theme"]["extend"]["colors"].update(colors)

    def add_color_palette(self, name: str, base_color: str) -> None:
        """Pełna paleta odcieni 50-950 dla koloru bazowego, oparta na zmiennych CSS."""
        if "colors" not in self.config["theme"]["extend"]:
            self.config["theme"]["extend"]["colors"] = {}

        self.config["theme"]["extend"]["colors"][name] = {
            "50": f"var(--color-{name}-50)",
            "100": f"var(--color-{name}-100)",
            "200": f"var(--color-{name}-200)",
            "300": f"var(--color-{name}-300)",
            "400": f"var(--color-{name}-400)",
            "500": f"var(--color-{name}-500)",
            "600": f"var(--color-{name}-600)",
            "700": f"var(--color-{name}-700)",
            "800": f"var(--color-{name}-800)",
            "900": f"var(--color-{name}-900)",
            "950": f"var(--color-{name}-950)",
        }

    def add_fonts(self, fonts: Dict[str, List[str]]) -> None:
        """Rodziny czcionek: rodzaj -> lista nazw rodzin."""
        if "fontFamily" not in self.config["theme"]["extend"]:
            self.config["theme"]["extend"]["fontFamily"] = {}

        self.config["theme"]["extend"]["fontFamily"].update(fonts)

    def add_spacing(self, spacing: Dict[str, str]) -> None:
        """Odstępy: nazwa -> wartość CSS."""
        if "spacing" not in self.config["theme"]["extend"]:
            self.config["theme"]["extend"]["spacing"] = {}

        self.config["theme"]["extend"]["spacing"].update(spacing)

    def add_breakpoints(self, breakpoints: Dict[str, str]) -> None:
        """Punkty łamania: nazwa -> szerokość."""
        if "screens" not in self.config["theme"]["extend"]:
            self.config["theme"]["extend"]["screens"] = {}

        self.config["theme"]["extend"]["screens"].update(breakpoints)

    def add_plugins(self, plugins: List[str]) -> None:
        """Wtyczki do wpisania w konfiguracji (bez duplikatów)."""
        for plugin in plugins:
            if plugin not in self.config["plugins"]:
                self.config["plugins"].append(plugin)

    def recommend_plugins(self) -> List[str]:
        """Zalecane wtyczki dla wybranego frameworka."""
        recommendations = []

        recommendations.append("tailwindcss-animate")

        if self.framework == "nextjs":
            recommendations.append("@tailwindcss/typography")

        return recommendations

    def generate_config_string(self) -> str:
        """Treść pliku konfiguracyjnego jako łańcuch."""
        if self.typescript:
            return self._generate_typescript()
        return self._generate_javascript()

    def _generate_typescript(self) -> str:
        """Konfiguracja w TypeScripcie."""
        plugins_str = self._format_plugins()

        # Wtyczki wychodzą z JSON-a i wracają jako require(...) w szablonie.
        config_obj = self.config.copy()
        config_obj.pop("plugins", None)
        config_json = json.dumps(config_obj, indent=2, ensure_ascii=False)

        wciete = self._indent_json(config_json, 1)
        przedrostek = f"{wciete},\n" if wciete else ""
        return f"""import type {{ Config }} from 'tailwindcss'

const config: Config = {{
{przedrostek}  plugins: [{plugins_str}],
}}

export default config
"""

    def _generate_javascript(self) -> str:
        """Konfiguracja w JavaScripcie."""
        plugins_str = self._format_plugins()

        config_obj = self.config.copy()
        config_obj.pop("plugins", None)
        config_json = json.dumps(config_obj, indent=2, ensure_ascii=False)

        wciete = self._indent_json(config_json, 1)
        przedrostek = f"{wciete},\n" if wciete else ""
        return f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
{przedrostek}  plugins: [{plugins_str}],
}}
"""

    def _format_plugins(self) -> str:
        """Lista wtyczek jako wywołania require(...).

        Nazwa wtyczki jest sprawdzana wzorcem nazwy pakietu npm: bez tego dowolny
        tekst z konfiguracji trafiałby do wygenerowanego kodu.
        """
        if not self.config["plugins"]:
            return ""

        plugin_requires = []
        for plugin in self.config["plugins"]:
            if not isinstance(plugin, str) or not _VALID_PLUGIN_NAME.match(plugin):
                raise ValueError(
                    f"niedozwolona nazwa wtyczki: {plugin!r} - nazwa musi być poprawną "
                    "nazwą pakietu npm (np. '@tailwindcss/typography')"
                )
            plugin_requires.append(f"require('{plugin}')")
        return ", ".join(plugin_requires)

    def _indent_json(self, json_str: str, level: int) -> str:
        """Wcięcie treści obiektu JSON bez otaczających nawiasów.

        Dla obiektu jednowierszowego (`{}`) nie ma czego wcinać - zwracany jest
        pusty łańcuch, a szablon nie stawia wtedy wiodącego przecinka.
        """
        lines = json_str.split("\n")
        if len(lines) < 3:
            return ""
        indent = "  " * level
        return "\n".join(indent + line for line in lines[1:-1])

    def write_config(self) -> tuple[bool, str]:
        """Zapisuje konfigurację. Zwraca (powodzenie, komunikat)."""
        try:
            config_content = self.generate_config_string()
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.write_text(config_content, encoding="utf-8")
        except ValueError as blad:
            return False, f"nie udało się zapisać konfiguracji: {blad}"
        except OSError as blad:
            return False, f"nie udało się zapisać konfiguracji: {blad}"
        return True, f"konfiguracja zapisana w {self.output_path}"

    def validate_config(self) -> tuple[bool, str]:
        """Kontrola konfiguracji. Zwraca (poprawna, komunikat)."""
        if not self.config["content"]:
            return False, "nie podano ścieżek content - Tailwind nie wie, co skanować"
        if not self.config["theme"]["extend"]:
            return True, f"{PREFIKS_OSTRZEZENIA} motyw nie ma żadnych rozszerzeń"
        return True, "konfiguracja poprawna"


def main() -> int:
    """Punkt wejścia wiersza poleceń."""
    parser = argparse.ArgumentParser(
        description="Generuje konfigurację Tailwind CSS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  python3 tailwind_config_gen.py --framework nextjs
  python3 tailwind_config_gen.py --js --colors brand:#3b82f6 accent:#8b5cf6
  python3 tailwind_config_gen.py --fonts display:"Playfair Display,serif"
  python3 tailwind_config_gen.py --spacing navbar:4rem --breakpoints 3xl:1920px
  python3 tailwind_config_gen.py --plugins
        """,
    )

    parser.add_argument(
        "--framework",
        choices=["react", "vue", "svelte", "nextjs"],
        default="react",
        help="framework docelowy (domyślnie react)",
    )

    parser.add_argument(
        "--js",
        action="store_true",
        help="konfiguracja w JavaScripcie zamiast TypeScriptu",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="ścieżka pliku wyjściowego",
    )

    parser.add_argument(
        "--colors",
        nargs="*",
        metavar="NAME:VALUE",
        help="kolory motywu, np. brand:#3b82f6",
    )

    parser.add_argument(
        "--fonts",
        nargs="*",
        metavar="TYPE:FAMILY",
        help="rodziny czcionek, np. sans:'Inter,system-ui'",
    )

    parser.add_argument(
        "--spacing",
        nargs="*",
        metavar="NAME:VALUE",
        help="odstępy, np. navbar:4rem",
    )

    parser.add_argument(
        "--breakpoints",
        nargs="*",
        metavar="NAME:WIDTH",
        help="punkty łamania, np. 3xl:1920px",
    )

    parser.add_argument(
        "--plugins",
        action="store_true",
        help="dodaj zalecane wtyczki",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="tylko kontrola, bez zapisu pliku",
    )

    args = parser.parse_args()

    # Jeśli --output wskazuje jawnie na rozszerzenie .js/.ts, rozszerzenie rozstrzyga
    # o formacie treści - inaczej "--output config.js" bez "--js" zapisałoby kod
    # TypeScript do pliku .js (i odwrotnie), co jest mylące dla narzędzi budowy.
    typescript = not args.js
    if args.output:
        sufiks = Path(args.output).suffix.lower()
        if sufiks == ".js" and typescript:
            print("Uwaga: --output ma rozszerzenie .js, generuję treść JavaScript "
                  "(nie TypeScript).", file=sys.stderr)
            typescript = False
        elif sufiks == ".ts" and not typescript:
            print("Uwaga: --output ma rozszerzenie .ts, generuję treść TypeScript "
                  "(--js zignorowane).", file=sys.stderr)
            typescript = True

    generator = TailwindConfigGenerator(
        typescript=typescript,
        framework=args.framework,
        output_path=args.output,
    )

    if args.colors:
        colors = {}
        for color_spec in args.colors:
            try:
                name, value = color_spec.split(":", 1)
                colors[name] = value
            except ValueError:
                print(f"niepoprawna specyfikacja koloru: {color_spec}", file=sys.stderr)
                sys.exit(1)
        generator.add_colors(colors)

    if args.fonts:
        fonts = {}
        for font_spec in args.fonts:
            try:
                font_type, family = font_spec.split(":", 1)
                fonts[font_type] = [f.strip().strip("'\"") for f in family.split(",")]
            except ValueError:
                print(f"niepoprawna specyfikacja czcionki: {font_spec}", file=sys.stderr)
                sys.exit(1)
        generator.add_fonts(fonts)

    if args.spacing:
        spacing = {}
        for spacing_spec in args.spacing:
            try:
                name, value = spacing_spec.split(":", 1)
                spacing[name] = value
            except ValueError:
                print(f"niepoprawna specyfikacja odstępu: {spacing_spec}", file=sys.stderr)
                sys.exit(1)
        generator.add_spacing(spacing)

    if args.breakpoints:
        breakpoints = {}
        for bp_spec in args.breakpoints:
            try:
                name, width = bp_spec.split(":", 1)
                breakpoints[name] = width
            except ValueError:
                print(f"niepoprawna specyfikacja punktu łamania: {bp_spec}", file=sys.stderr)
                sys.exit(1)
        generator.add_breakpoints(breakpoints)

    if args.plugins:
        recommended = generator.recommend_plugins()
        generator.add_plugins(recommended)
        print(f"dodano zalecane wtyczki: {', '.join(recommended)}")
        print("\nZainstaluj poleceniem:")
        print(f"  npm install -D {' '.join(recommended)}")

    valid, message = generator.validate_config()
    if not valid:
        print(f"kontrola konfiguracji nie przeszła: {message}", file=sys.stderr)
        sys.exit(1)

    if message.startswith(PREFIKS_OSTRZEZENIA):
        print(message)

    if args.validate_only:
        print("konfiguracja poprawna")
        print("\nWygenerowana treść:")
        print(generator.generate_config_string())
        return 0

    success, message = generator.write_config()
    print(message)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
