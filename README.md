# TermUI

A `rich` + `prompt_toolkit` terminal UI library for AI agent interactions.

## Install

```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"

# Or install from source
pip install .
```

## Package layout

```
termui/
├── __init__.py      # flat public API re-exports
├── console.py       # shared rich.Console singleton
├── theme.py         # ThemeConfig, Theme enum, apply_theme()
├── output.py        # all rich output helpers
├── input.py         # all prompt_toolkit input helpers
├── layout.py        # columns, live_dashboard, DashboardLayout
├── logging.py       # RichHandler, get_logger()
├── notify.py        # notify(), NotifyLevel
└── diff.py          # print_diff(), print_diff_files()
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
| `print_table(headers, rows, *, title, caption, show_lines, …)` | Rich table |
| `print_key_value(data, *, title, key_style, value_style)` | Aligned key/value pairs |
| `print_tree(label, data, *, guide_style)` | Nested dict as tree |
| `print_json(data, *, indent, highlight)` | Pretty-print JSON |
| `print_syntax(code, language, *, title, line_numbers, theme, highlight_lines)` | Syntax highlight |
| `spinner(text, *, spinner_name, style)` | Animated spinner context manager |
| `progress_bar(description, *, total, show_time)` | Progress context manager |
| `progress_track(iterable, *, description)` | Wrap an iterable with a progress bar |

### `termui.input` — prompt_toolkit input

| Function | Description |
|---|---|
| `ask_input(prompt, *, default, validator, allow_empty)` | Text prompt |
| `ask_secret(prompt, *, confirm)` | Masked password prompt |
| `ask_int(prompt, *, default, min_value, max_value)` | Integer prompt |
| `ask_float(prompt, *, default, min_value, max_value)` | Float prompt |
| `ask_confirm(prompt, *, default)` | Yes/No prompt |
| `ask_file(prompt, *, extensions, must_exist)` | File path + tab-complete |
| `ask_directory(prompt, *, must_exist, create_if_missing)` | Directory path |
| `ask_select(prompt, options, *, default)` | Numbered single-choice |
| `ask_multiselect(prompt, options, *, min_choices, max_choices)` | Multi-choice |
| `ask_autocomplete(prompt, completions, *, fuzzy, allow_free_text)` | Autocomplete prompt |
| `ask_editor(prompt, *, initial_text, extension, editor)` | Open `$EDITOR` |
| `ask_form(fields)` | Collect multiple fields at once |

### `termui.theme`

```python
from termui.theme import apply_theme, Theme, ThemeConfig

apply_theme(Theme.MONOKAI)   # DARK | LIGHT | MONOKAI | SOLARIZED | PLAIN

# Custom theme
apply_theme(ThemeConfig(success="bold #a6e22e", error="bold #f92672"))
```

### `termui.layout`

```python
from termui import columns, live_dashboard
from termui.layout import DashboardLayout, pager

# Side-by-side panels
columns(panel_a, panel_b)

# Live-updating display
with live_dashboard(refresh_per_second=4) as live:
    live.update(build_table())

# Named split-pane dashboard
dash = DashboardLayout()
dash.add_section("header", size=3).add_section("body").add_section("footer", size=2)
with dash.live() as live:
    dash["header"].update(Panel("My App"))
    dash["body"].update(my_table)
```

### `termui.logging`

```python
from termui.logging import get_logger
log = get_logger("agent", show_path=True)
log.info("Ready")
log.warning("Context at 80 %%")
log.error("Timeout", exc_info=True)
```

### `termui.notify`

```python
from termui.notify import notify, NotifyLevel
notify("Task complete", level=NotifyLevel.SUCCESS)
notify("Disk almost full", level=NotifyLevel.WARNING, duration=5)
```

### `termui.diff`

```python
from termui.diff import print_diff, print_diff_files
print_diff(old_code, new_code, language="python", mode="side-by-side")
print_diff_files("v1.py", "v2.py")
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
])
```
