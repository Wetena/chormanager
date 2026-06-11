# 🤖 Coding Agent Instructions: Choraufstellung App

## 🏗️ 1. Architektur-Prinzipien (STRIKT)
| Modul | Verantwortlichkeit | Qt-Imports erlaubt? | Testbarkeit |
|-------|-------------------|---------------------|-------------|
| `src/core/` | Reine Business-Logik: Grid-Math, Sortierung, Swap-Algorithmen, Cost-Funktionen, Commands | ❌ NEIN | ✅ 100% Unit-Testbar (headless) |
| `src/ui/` | PyQt5-Dialoge, Widgets, Event-Handler. Dünne Wrapper. | ✅ JA | ⚠️ Nur `pytest-qt` für kritische Flows |
| `src/main.py` | Application Shell: UI-Wiring, State-Management, Menü, Undo-Stack, Auto-Save | ✅ JA | 🔍 Integration-Tests (I/O, Theme, Dialogs) |

- **Kein globaler State.** Übergabe per Constructor/Dependency Injection.
- **`main.py` ≤ 750 Zeilen.** Auslagerung in `core/` oder `ui/` erzwingen.
- **`QUndoCommand` für jede zustandsverändernde Aktion.** Keine direkten Mutationen in `main.py` oder Widgets.

## 🧪 2. TDD-Workflow (NON-NEGOTIABLE)
1. **RED:** Schreibe zuerst failing test(s) in `tests/unit/`, `tests/integration/` oder `tests/ui/`.
2. **GREEN:** Implementiere minimalen Code, um Tests grün zu machen.
3. **REFACTOR:** Bereinige Code, extrahiere Funktionen, füge Type Hints/Docstrings hinzu. Tests bleiben grün.
4. **KEIN Feature ohne Tests.** Neue Logik ohne zugehörige Tests wird abgelehnt.
5. **Test-Pyramide:** ~70% Unit (`core/`), ~25% Integration (`storage/`, `config/`), ~5% UI (`pytest-qt`).
6. **Headless Execution:** `QT_QPA_PLATFORM=offscreen` für lokale/CI-Läufe. Kein Display-Server nötig.

## 📝 3. Code-Generierungsstandards
- **Type Hints:** `typing` Modul für alle Signaturen (`def run(grid: FormationGrid, rules: list[str]) -> bool:`).
- **Docstrings:** Public APIs müssen Zweck, Parameter, Return und Exceptions dokumentieren.
- **Error Handling:** `try/except` mit spezifischen Exceptions. Fallback-Werte. Niemals `except: pass`.
- **File I/O:** Atomic writes (`tmp` + `os.replace`). XDG-Pfade (`~/.local/share/choraufstellung/`).
- **Keine Platzhalter:** `# ... hier Logik` oder `TODO` in produktivem Code verboten. Vollständig lauffähig.
- **API-Kompatibilität:** Bestehende Signaturen nicht brechen. Wraps/Adapter nutzen, falls Refactor nötig.

## 🔒 4. Safety & Integration Guards
- ✅ `python -m py_compile src/main.py` muss fehlerfrei durchlaufen.
- ✅ `python -m pytest tests/ -q` muss grün bleiben (0 failed).
- ❌ Keine Änderung an `src/core/` ohne entsprechende Unit-Tests.
- ❌ UI-Änderungen dürfen Drag & Drop, Rubber-Band, Theming oder Layout nicht brechen.
- ❌ Keine `QApplication`-Mocking, wo reine Python-Logik ausreicht.
- 🔄 Atomic Saves & Rollback bei I/O-Fehlern. Statusbar/Logs bei Recovery.

## 📤 5. Erwartetes AI-Output-Format
```text
# FILE: src/core/new_module.py
[EXAKTER CODE]

# FILE: tests/unit/test_new_module.py
[EXAKTE TESTS]

# FILE: src/main.py (ERGÄNZUNG)
# --- NEW: Integration ...
[DIFF/EINFÜGESTELLE]

✅ ARCHITEKTUR-HINWEIS: [1-2 Sätze, warum dieser Ansatz gewählt wurde]

- Zeige klar, wo Code ergänzt wird (# --- NEW: ...).
- Liefere vollständige, kopierfertige Dateien.
- Erkläre Designentscheidungen kurz im Kommentar.
- Respektiere bestehende Imports, Signale/Slots, Klassenstruktur.

## 6. Pre-Flight Checklist (AI prüft vor Ausgabe)

- Tests geschrieben & rot?
- src/core/ frei von Qt-Imports?
- Type Hints & Docstrings vorhanden?
- Error Handling & Fallbacks implementiert?
- py_compile + pytest würden lokal durchlaufen?
- Keine Platzhalter, kein "TODO", keine Globalen?
- Undo/Redo via QUndoCommand für State-Changes?
- XDG-Pfade & atomic I/O bei Dateien?

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **chormanager** (2671 symbols, 4677 relationships, 144 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/chormanager/context` | Codebase overview, check index freshness |
| `gitnexus://repo/chormanager/clusters` | All functional areas |
| `gitnexus://repo/chormanager/processes` | All execution flows |
| `gitnexus://repo/chormanager/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
