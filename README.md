# TermUI

A `rich` + `prompt_toolkit` terminal UI library for AI agent interactions.

**Thread-safe** • **Typed** (`py.typed`) • **89 public symbols** • **Python 3.10+**

## Install

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install with clipboard support
pip install -e ".[clipboard]"

# Install from source
pip install .
```

## Package layout

```
termui/
├── py.typed                # PEP 561 marker
├── __init__.py             # flat public API re-exports (89 symbols)
├── console.py              # shared rich.Console singleton, thread-safe lock
├── theme.py                # ThemeConfig, Theme enum, registry, serialization
├── output.py               # rich output helpers (tables, metrics, timelines…)
├── input.py                # prompt_toolkit input (text, date, email, url…)
├── layout.py               # columns, grid, live dashboards, scrollable panels
├── termui_logging.py       # RichHandler, structured fields, file logging
├── notify.py               # toast notifications, history, queue, sticky
├── diff.py                 # unified/side-by-side diffs, char-level, dirs
├── table_stream.py         # streaming live table with in-place updates
├── confirm_panel.py        # rich confirmation panels for destructive actions
└── clipboard.py            # clipboard copy/paste (optional pyperclip)
```

## Quick start

```python
import termui as ui

ui.print_header("My Agent", subtitle="v2.0")
ui.print_info("Loading model…")

with ui.spinner("Thinking…"):
    result = call_llm(prompt)

ui.print_markdown(result)
ui.print_success("Done")
```

## Features

### Thread-safe console

All output goes through a shared `Console` with `console_lock` (`threading.RLock`).

```python
from termui import locked_console

with locked_console() as con:
    con.print("Thread-safe output")
```

### Environment awareness

- **`NO_COLOR`** / **`TERM=dumb`** → colours, spinners, and progress bars are disabled automatically.
- **`UI_FORCE_TERMINAL`** → force rich terminal mode.

## Module reference

### `termui.output` — rich output

| Function | Description |
|---|---|
| `print_text(text, style)` | Plain print with optional rich style |
| `print_success/error/warning/info(text)` | Coloured semantic messages |
| `print_panel(text, *, title, subtitle, style, expand, padding)` | Box with border |
| `print_markdown(text)` | Render Markdown |
| `print_rule(title, *, style, align)` | Horizontal separator |
| `print_header(title, subtitle)` | Full-width header banner |
| `print_table(headers, rows, *, zebra, footer_row, max_col_width)` | Rich table with optional zebra/footer |
| `print_key_value(data, *, title)` | Aligned key/value pairs |
| `print_tree(label, data)` | Nested dict as tree |
| `print_json(data, *, highlight_path)` | Pretty-print JSON with key emphasis |
| `print_syntax(code, language, *, highlight_lines)` | Syntax highlighting |
| `print_status_grid(statuses)` | Service status grid (✔/✘) |
| `print_metric(label, value, *, unit, delta)` | Single metric card |
| `print_metric_group(metrics)` | Side-by-side metric cards |
| `print_timeline(events, *, width)` | Horizontal timeline chart |
| `print_callout(text, *, kind)` | Tip/note/warning/danger callout |
| `spinner(text)` | Animated spinner context manager |
| `progress_bar(description, *, total)` | Progress context manager |
| `progress_track(iterable, *, description)` | Wrap iterable with a progress bar |
| `progress_map(fn, items, *, max_workers)` | Parallel map with progress |
| `spinner_group(tasks)` | Concurrent spinners context manager |

### `termui.input` — prompt_toolkit input

| Function | Description |
|---|---|
| `ask_input(prompt, *, default, validator, history)` | Text prompt |
| `ask_secret(prompt, *, confirm, show_strength)` | Masked password prompt |
| `ask_int(prompt, *, min_value, max_value)` | Integer prompt |
| `ask_float(prompt, *, min_value, max_value)` | Float prompt |
| `ask_confirm(prompt, *, default)` | Yes/No prompt |
| `ask_file(prompt, *, extensions, must_exist)` | File path + tab-complete |
| `ask_directory(prompt, *, must_exist, create_if_missing)` | Directory path |
| `ask_select(prompt, options)` | Numbered single-choice |
| `ask_multiselect(prompt, options)` | Multi-choice (comma-separated) |
| `ask_select_interactive(prompt, options)` | Arrow-key single-choice |
| `ask_multiselect_interactive(prompt, options)` | Arrow-key multi-choice |
| `ask_date(prompt, *, fmt)` | Date prompt with format validation |
| `ask_datetime(prompt, *, fmt)` | Datetime prompt |
| `ask_url(prompt)` | URL prompt with validation |
| `ask_email(prompt)` | Email prompt with validation |
| `ask_autocomplete(prompt, completions)` | Fuzzy autocomplete |
| `ask_editor(prompt)` | Open `$EDITOR` |
| `ask_form(fields)` | Multi-field form with validation & conditional fields |

### `termui.theme`

```python
from termui import apply_theme, Theme, ThemeConfig, theme_context

apply_theme(Theme.MONOKAI)   # DARK | LIGHT | MONOKAI | SOLARIZED | PLAIN

# Custom theme
from termui import register_theme
register_theme("ocean", ThemeConfig(success="bold #a6e22e", error="bold #f92672"))
apply_theme("ocean")

# Temporary theme switch
with theme_context(Theme.LIGHT):
    print_info("This uses the light theme")

# Serialization
from termui import save_theme, load_theme
save_theme(ThemeConfig(), "my_theme.json")
cfg = load_theme("my_theme.json")
```

### `termui.layout`

```python
from termui import columns, grid, split_horizontal, live_table, scrollable_panel

# Side-by-side panels
columns(panel_a, panel_b)

# NxM grid
grid([[Panel("A"), Panel("B")], [Panel("C"), Panel("D")]])

# Two-pane split
split_horizontal(Panel("Top"), Panel("Bottom"), ratio=(2, 1))

# Live-updating table
with live_table(["Step", "Status"]) as lt:
    lt.add_row("1", "running")
    lt.add_row("2", "done")

# Scrollable panel (shows last N lines)
scrollable_panel(long_text, height=10)

# Named dashboard
from termui import DashboardLayout
dash = DashboardLayout()
dash.add_section("header", size=3).add_section("body").add_section("footer", size=2)
with dash.live() as live:
    dash.update("header", Panel("My App"))
    dash.update("body", my_table)
```

### `termui.termui_logging`

```python
from termui import get_logger, set_level, capture_logs

log = get_logger("agent", show_path=True, log_file="agent.log")
log.info("Ready")
log.info("Request", extra={"fields": {"status": 200, "ms": 42}})

# Temporarily capture logs for testing
with capture_logs("agent") as records:
    log.info("captured")
assert len(records) == 1
```

### `termui.notify`

```python
from termui import notify, NotifyLevel, NotifyQueue, sticky_notify

notify("Task complete", level=NotifyLevel.SUCCESS, bell=True)
notify("Disk almost full", level=NotifyLevel.WARNING, duration=5)

# Notification history
from termui import notification_history, replay_notifications
history = notification_history(n=10)
replay_notifications()

# Batch notifications
q = NotifyQueue()
q.put("step 1 done")
q.put("step 2 done")
q.flush()

# Sticky banner (persists until context exits)
with sticky_notify("Build in progress…"):
    do_build()
```

### `termui.diff`

```python
from termui import print_diff, print_diff_files, print_diff_dirs, diff_summary

print_diff(old_code, new_code, mode="side-by-side", char_highlight=True)
print_diff_files("v1.py", "v2.py", ignore_whitespace=True)
print_diff_dirs("project_v1", "project_v2", extensions=[".py"])

s = diff_summary(old_code, new_code)
print(f"+{s.added} -{s.removed} ~{s.changed}")
```

### `termui.table_stream`

```python
from termui import StreamingTable

with StreamingTable(["Step", "Status", "Time"]) as st:
    idx = st.add_row("1", "running", "0s")
    st.update_cell(idx, 1, "✔ done")
```

### `termui.confirm_panel`

```python
from termui import confirm_action

if confirm_action("Delete all logs?", details="This cannot be undone."):
    delete_logs()
```

### `termui.clipboard`

```python
from termui import copy_to_clipboard, paste_from_clipboard, clipboard_available

if clipboard_available():
    copy_to_clipboard("Hello!")
    text = paste_from_clipboard()
```

## `ask_form` example

```python
result = ui.ask_form([
    {"name": "name",     "prompt": "Your name"},
    {"name": "password", "prompt": "Password",   "type": "secret",  "confirm": True},
    {"name": "age",      "prompt": "Age",         "type": "int",     "min_value": 0},
    {"name": "model",    "prompt": "LLM model",   "type": "select",
     "options": ["gpt-4o", "claude-3-5-sonnet", "mistral-large"]},
    {"name": "features", "prompt": "Features",    "type": "multiselect",
     "options": ["streaming", "tools", "vision", "caching"]},
    {"name": "deadline", "prompt": "Deadline",    "type": "text",
     "depends_on": {"field": "features", "value": ["streaming"]}},
])
```

## Running tests

```bash
pytest tests/ -v
```
