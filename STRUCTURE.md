# Project Structure

This project follows the modern Python package layout with `src/` directory structure.
Python 3.10+ is required. The package ships a `py.typed` marker for PEP 561 compliance.

```
termui/
│
├── pyproject.toml            # Project config (PEP 517/518), deps, mypy, ruff
├── README.md                 # Project description & full API reference
├── STRUCTURE.md              # This file
├── LICENSE                   # MIT License
├── .gitignore                # Git ignored files
├── requirements.txt          # Legacy requirements (optional)
│
├── src/                      # Source code
│   └── termui/               # Main package
│       ├── py.typed                  # PEP 561 type-hint marker
│       ├── __init__.py               # Public API re-exports (89 symbols)
│       ├── console.py                # Shared rich.Console singleton, thread-safe lock
│       ├── theme.py                  # ThemeConfig, Theme enum, registry, serialization
│       ├── output.py                 # Rich output helpers (tables, metrics, timelines…)
│       ├── input.py                  # Prompt-toolkit input (text, date, url, email…)
│       ├── layout.py                 # Columns, grid, live dashboards, scrollable panels
│       ├── termui_logging.py         # RichHandler, structured fields, file logging
│       ├── notify.py                 # Toast notifications, history, queue, sticky
│       ├── diff.py                   # Unified/side-by-side diffs, char-level, dirs
│       ├── table_stream.py           # Streaming live table with in-place cell updates
│       ├── confirm_panel.py          # Rich confirmation panels for destructive actions
│       └── clipboard.py              # Clipboard copy/paste (optional pyperclip)
│
├── tests/                    # Unit tests (90 tests)
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures (capture_console, theme reset)
│   ├── test_output.py        # Output helpers tests
│   ├── test_theme.py         # Theme management tests
│   ├── test_diff.py          # Diff rendering tests
│   ├── test_logging.py       # Logging handler tests
│   ├── test_notify.py        # Notification tests
│   ├── test_layout.py        # Layout helpers tests
│   ├── test_table_stream.py  # Streaming table tests
│   └── test_clipboard.py     # Clipboard tests
│
├── scripts/                  # CLI and helper scripts
│   └── demo.py               # Comprehensive demo of all features
│
└── docs/                     # Documentation
    └── getting_started.md
```

## Key architectural decisions

- **Thread safety** — All console output is guarded by `console_lock` (`threading.RLock`). Use `locked_console()` for atomic multi-print sequences.
- **Environment variables** — `NO_COLOR` and `TERM=dumb` disable colours, spinners, and progress bars automatically. `UI_FORCE_TERMINAL` forces rich terminal mode.
- **Typed** — The package includes `py.typed` and targets `mypy --strict`.
- **Optional dependencies** — Clipboard support (`pyperclip`) is optional and degrades gracefully with a clear `ImportError`.

## Installation

```bash
# Install in development mode (editable)
pip install -e .

# Install with dev dependencies (mypy, pytest, pytest-rich)
pip install -e ".[dev]"

# Install with clipboard support
pip install -e ".[clipboard]"

# Install from source
pip install .
```

## Usage

```python
from termui import print_header, print_success, spinner

print_header("My App", subtitle="v1.0")

with spinner("Processing..."):
    # do work
    pass

print_success("Done!")
```

## Running the demo

```bash
python scripts/demo.py
```

## Running tests

```bash
pytest tests/ -v
```

## Module summary

| Module | Public symbols | Description |
|---|---|---|
| `console` | 5 | Shared Console singleton, lock, env helpers |
| `theme` | 10 | Theme enum, config, registry, context manager, serialization |
| `output` | 22 | Tables, panels, metrics, timelines, spinners, progress |
| `input` | 18 | Text, numeric, date, email, URL, select, form |
| `layout` | 11 | Grid, columns, split, live table, scrollable panel, dashboard |
| `termui_logging` | 4 | RichHandler, structured fields, file handler, capture |
| `notify` | 6 | Toast notifications, history, queue, sticky banner |
| `diff` | 5 | Unified/side-by-side diffs, char-level, summary, dirs |
| `table_stream` | 1 | StreamingTable with live updates |
| `confirm_panel` | 1 | Rich confirmation panels |
| `clipboard` | 3 | Copy/paste with graceful degradation |

## Benefits of this structure

1. **Modern Standard** — Follows PEP 517/518 with `pyproject.toml`
2. **Isolated Source** — `src/` layout prevents accidental imports
3. **Clean Namespace** — Package installed properly via pip
4. **Fully Typed** — `py.typed` marker, targets `mypy --strict`
5. **Thread-Safe** — All output guarded by `console_lock`
6. **Testable** — 90 tests, shared fixtures, capture helpers
7. **Distributable** — Ready for PyPI publishing
