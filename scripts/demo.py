#!/usr/bin/env python3
"""termui demo — exercises every public API in the library.

Run:  python scripts/demo.py
"""

import time
import tempfile
import os
from datetime import datetime
from termui import (
    # output
    print_text, print_panel, print_markdown, print_success,
    print_error, print_warning, print_info,
    print_table, print_tree, print_json, print_syntax,
    print_rule, print_key_value, spinner, progress_bar, progress_track,
    print_callout, print_metric, print_metric_group, print_status_grid,
    print_timeline, progress_map, spinner_group, SpinnerGroup,
    # layout
    columns, live_dashboard, clear_screen, print_header,
    grid, scrollable_panel, split_horizontal, live_table, LiveTable,
    # logging
    get_logger, RichHandler, capture_logs, set_level,
    # notify
    notify, sticky_notify, notification_history, replay_notifications,
    # diff
    print_diff, print_diff_files, print_diff_dirs, diff_summary, DiffSummary,
    # theme
    Theme, apply_theme, get_theme, current_theme_name, list_themes,
    theme_context, ThemeConfig, register_theme, save_theme, load_theme,
    # input
    ask_input, ask_confirm, ask_select, ask_multiselect, ask_int, ask_float,
    ask_secret, ask_email, ask_url, ask_file, ask_directory, ask_date,
    ask_datetime, ask_autocomplete, ask_editor, ask_form,
    ask_select_interactive, ask_multiselect_interactive,
    # clipboard
    clipboard_available, copy_to_clipboard, paste_from_clipboard,
    # confirm_panel
    confirm_action,
    # table_stream
    StreamingTable,
    # console
    console, get_console, is_dumb_terminal, console_lock, locked_console,
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

print_info(f"Current theme: {current_theme_name()}")
print_info(f"Available themes: {', '.join(list_themes())}")

# Theme context manager
with theme_context(Theme.LIGHT):
    print_info("Inside LIGHT theme context")
print_info("Back to DARK theme")


# ── Basic output ─────────────────────────────────────────────────────
separator("2. Semantic output")
print_success("Everything is fine")
print_warning("Approaching rate limit (80 %)")
print_error("API returned 429 — retrying")
print_info("Loaded 42 documents from index")

separator("3. Panel, Markdown & Text")
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
print_text("[bold green]Plain text output[/bold green] with Rich markup support")

separator("3b. Callout")
print_callout(
    "This is an important callout message!",
    kind="tip",
    title="💡 Tip",
)


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


# ── Columns & Grid ──────────────────────────────────────────────────
separator("13. Columns")
from rich.panel import Panel as RPanel
columns(
    RPanel("[cyan]Left pane[/cyan]\nModel output here", title="Output"),
    RPanel("[yellow]Right pane[/yellow]\nMetrics here",  title="Metrics"),
)

separator("13b. Grid")
grid([
    [RPanel("[red]A[/red]", title="1"), RPanel("[green]B[/green]", title="2")],
    [RPanel("[blue]C[/blue]", title="3"), RPanel("[yellow]D[/yellow]", title="4")],
])

separator("13c. Split Horizontal")
split_horizontal(
    RPanel("[magenta]Top section[/magenta]", title="Header"),
    RPanel("[cyan]Bottom section[/cyan]", title="Content"),
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
print_info(f"Is dumb terminal: {is_dumb_terminal}")

# ── Metrics ──────────────────────────────────────────────────────────
separator("17. Metrics")
print_metric("Response Time", 245, unit="ms", delta=-12.0)
print_metric("Error Rate", 0.3, unit="%", delta=0.1)

print_metric_group([
    {"label": "Requests", "value": "1,234"},
    {"label": "Success", "value": "98.7%"},
    {"label": "Avg Latency", "value": "156ms"},
])

# ── Status Grid ──────────────────────────────────────────────────────
separator("18. Status Grid")
print_status_grid(
    {
        "Database": "✓ Connected",
        "Cache": "✓ Redis OK",
        "API": "⚠ Degraded",
        "Queue": "✓ Processing",
    },
    title="System Status",
)

# ── Timeline ─────────────────────────────────────────────────────────
separator("19. Timeline")
print_timeline([
    {"label": "Batch Job", "start": 0, "end": 30},
    {"label": "Processing", "start": 15, "end": 30},
    {"label": "Cleanup", "start": 25, "end": 35},
], title="Job Timeline")

# ── Spinner Group ────────────────────────────────────────────────────
separator("20. Spinner Group")
with spinner_group() as sg:
    s1 = sg.add("Task 1")
    s2 = sg.add("Task 2")
    time.sleep(0.5)
    s1.update("Task 1 - Processing")
    time.sleep(0.5)
    s1.done()
    time.sleep(0.5)
    s2.done()

# ── Progress Map ─────────────────────────────────────────────────────
separator("21. Progress Map")
def process_item(x):
    time.sleep(0.05)
    return x * 2

results = progress_map(process_item, [1, 2, 3, 4, 5], description="Processing")
print_info(f"Results: {results}")

# ── Streaming Table ──────────────────────────────────────────────────
separator("22. Streaming Table")
with StreamingTable(["ID", "Name", "Status"]) as st:
    for i in range(5):
        st.add_row(str(i+1), f"Item {i+1}", "✓")
        time.sleep(0.1)

# ── Clipboard ────────────────────────────────────────────────────────
separator("23. Clipboard")
if clipboard_available():
    test_text = "termui clipboard test"
    copy_to_clipboard(test_text)
    print_success(f"Copied to clipboard: {test_text}")
    pasted = paste_from_clipboard()
    print_info(f"Pasted from clipboard: {pasted}")
else:
    print_warning("Clipboard not available")

# ── Diff Files & Dirs ────────────────────────────────────────────────
separator("24. Diff Summary")
old_text = "Hello world\nThis is old\n"
new_text = "Hello world\nThis is new\nExtra line\n"
summary = diff_summary(old_text, new_text)
print_info(f"Diff: +{summary.added} -{summary.removed} ~{summary.changed}")

# ── Console Functions ────────────────────────────────────────────────
separator("25. Console")
c = get_console()
print_info(f"Console width: {c.width}")
with locked_console() as lc:
    lc.print("[bold]Thread-safe console output[/bold]")

# ── Sticky Notifications ─────────────────────────────────────────────
separator("26. Sticky Notifications")
sticky_notify("This is a persistent notification", level=NotifyLevel.INFO)
time.sleep(0.5)
history = notification_history()
print_info(f"Notification history: {len(history)} notifications")

# ── Live Table ───────────────────────────────────────────────────────
separator("27. Live Table")
with live_table(["Metric", "Value"], title="Live Metrics") as lt:
    lt.add_row("CPU", "50%")
    time.sleep(0.3)
    lt.add_row("Memory", "60%")
    time.sleep(0.3)
    lt.add_row("Disk", "75%")
    time.sleep(0.3)

# ── Scrollable Panel ─────────────────────────────────────────────────
separator("28. Scrollable Panel")
long_content = "\n".join([f"Line {i+1}" for i in range(5)])
scrollable_panel(long_content, title="Scrollable Content", height=3)

print_rule()
print_success("termui demo complete! All functions demonstrated.")
