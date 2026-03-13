#!/usr/bin/env python3
"""termui demo — exercises every public API in the library.

Run:  python scripts/demo.py
"""

import time
from termui import (
    # output
    print_text, print_panel, print_markdown, print_success,
    print_error, print_warning, print_info,
    print_table, print_tree, print_json, print_syntax,
    print_rule, print_key_value, spinner, progress_bar, progress_track,
    # layout
    columns, live_dashboard, clear_screen, print_header,
    # logging
    get_logger,
    # notify
    notify,
    # diff
    print_diff,
    # theme
    Theme, apply_theme,
)
from termui.notify import NotifyLevel
from termui.layout import DashboardLayout, pager, terminal_size

# ────────────────────────────────────────────────────────────────────
log = get_logger("demo", show_path=True)


def separator(label: str) -> None:
    print_rule(label, align="left")


# ── Theme ────────────────────────────────────────────────────────────
separator("1. Themes")
for t in Theme:
    apply_theme(t)
    print_info(f"  Active theme: {t.name}")
apply_theme(Theme.DARK)  # back to default


# ── Basic output ─────────────────────────────────────────────────────
separator("2. Semantic output")
print_success("Everything is fine")
print_warning("Approaching rate limit (80 %)")
print_error("API returned 429 — retrying")
print_info("Loaded 42 documents from index")

separator("3. Panel & Markdown")
print_panel(
    "Welcome to [bold cyan]termui[/bold cyan] — a rich terminal UI library.",
    title="About",
    subtitle="v1.0.0",
)
print_markdown("""
## Features
- Rich **panels**, tables, trees, and diffs
- Prompt-toolkit input with fuzzy autocomplete
- Live dashboards and progress bars
""")


# ── Table ────────────────────────────────────────────────────────────
separator("4. Table")
print_table(
    ["Model", "Tokens", "Latency (ms)", "Cost ($)"],
    [
        ("gpt-4o",           "8 192",  "320",  "0.0120"),
        ("claude-3-5-sonnet","200 000","280",  "0.0150"),
        ("mistral-large",    "32 768", "210",  "0.0080"),
    ],
    title="Model Comparison",
    show_lines=True,
)


# ── Key-value ────────────────────────────────────────────────────────
separator("5. Key-value pairs")
print_key_value(
    {
        "Agent":      "ResearchAgent",
        "Model":      "claude-sonnet-4-20250514",
        "Max tokens": 4096,
        "Temperature": 0.7,
        "Streaming":  True,
    },
    title="Config",
)


# ── Tree ─────────────────────────────────────────────────────────────
separator("6. Tree")
print_tree("Agent Graph", {
    "PlannerAgent": {
        "tools": ["web_search", "calculator"],
        "sub-agents": {
            "WriterAgent": {"tools": ["file_write"]},
            "CodeAgent":   {"tools": ["bash", "python_repl"]},
        },
    },
})


# ── JSON ─────────────────────────────────────────────────────────────
separator("7. JSON")
print_json({"status": "ok", "tokens_used": 1234, "model": "claude"})


# ── Syntax highlight ─────────────────────────────────────────────────
separator("8. Syntax")
print_syntax(
    'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n',
    "python",
    title="greet.py",
    highlight_lines={1},
)


# ── Diff ─────────────────────────────────────────────────────────────
separator("9. Diff")
OLD = 'def greet(name):\n    return "Hello " + name\n'
NEW = 'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n'
print_diff(OLD, NEW, title_old="greet_v1.py", title_new="greet_v2.py", language="python")


# ── Spinner ──────────────────────────────────────────────────────────
separator("10. Spinner")
with spinner("Calling LLM API…") as s:
    time.sleep(1.5)
    s.update("[bold]Post-processing response…[/bold]")
    time.sleep(1.0)
print_success("Done")


# ── Progress bar ─────────────────────────────────────────────────────
separator("11. Progress bar")
with progress_bar("Embedding docs", total=20) as bar:
    task = bar.add_task("chunk", total=20)
    for _ in range(20):
        time.sleep(0.05)
        bar.advance(task)


# ── progress_track ───────────────────────────────────────────────────
separator("12. progress_track")
items = list(range(10))
for item in progress_track(items, description="Indexing…"):
    time.sleep(0.05)


# ── Columns ──────────────────────────────────────────────────────────
separator("13. Columns")
from rich.panel import Panel as RPanel
columns(
    RPanel("[cyan]Left pane[/cyan]\nModel output here", title="Output"),
    RPanel("[yellow]Right pane[/yellow]\nMetrics here",  title="Metrics"),
)


# ── Notifications ────────────────────────────────────────────────────
separator("14. Notify")
notify("Index built successfully", level=NotifyLevel.SUCCESS)
notify("Cache miss rate > 20 %",   level=NotifyLevel.WARNING)
notify("Connection to DB lost",    level=NotifyLevel.ERROR, title="DB Alert")


# ── Logging ──────────────────────────────────────────────────────────
separator("15. Structured logging")
log.debug("Loading tokenizer")
log.info("Model warmed up — ready to serve")
log.warning("Context at 78 %% capacity")
log.error("Upstream timeout after 30 s")


# ── Terminal info ────────────────────────────────────────────────────
separator("16. Terminal info")
cols, lines = terminal_size()
print_info(f"Terminal size: {cols} × {lines}")

print_rule()
print_success("termui demo complete!")
