"""termui — A rich terminal UI library for AI agent interactions.

Modules
-------
clipboard       Clipboard copy/paste with graceful degradation.
confirm_panel   Rich confirmation panels for destructive actions.
console         Shared ``rich`` Console singleton with thread-safe locking.
diff            Side-by-side, unified, and directory diff rendering.
input           Prompt-toolkit input helpers: text, confirm, select, file, form …
layout          Multi-column layouts, grids, live dashboards, scrollable panels.
notify          In-terminal toast notifications with history and queuing.
output          High-level output: panels, tables, trees, progress, markdown …
table_stream    Streaming table for incremental row display.
theme           Centralized colour / style theme with light/dark switching.
termui_logging  Drop-in structured log handler that renders through rich.
"""

# ── console ──────────────────────────────────────────────────────────
from .console import (                             # noqa: F401
    console,
    console_lock,
    get_console,
    is_dumb_terminal,
    locked_console,
)

# ── theme ────────────────────────────────────────────────────────────
from .theme import (                               # noqa: F401
    Theme,
    ThemeConfig,
    apply_theme,
    current_theme_name,
    get_theme,
    list_themes,
    load_theme,
    register_theme,
    save_theme,
    theme_context,
)

# ── output ───────────────────────────────────────────────────────────
from .output import (                              # noqa: F401
    SpinnerGroup,
    print_callout,
    print_error,
    print_header,
    print_info,
    print_json,
    print_key_value,
    print_markdown,
    print_metric,
    print_metric_group,
    print_panel,
    print_rule,
    print_status_grid,
    print_success,
    print_syntax,
    print_table,
    print_text,
    print_timeline,
    print_tree,
    print_warning,
    progress_bar,
    progress_map,
    progress_track,
    spinner,
    spinner_group,
)

# ── input ────────────────────────────────────────────────────────────
from .input import (                               # noqa: F401
    ask_autocomplete,
    ask_confirm,
    ask_date,
    ask_datetime,
    ask_directory,
    ask_editor,
    ask_email,
    ask_file,
    ask_float,
    ask_form,
    ask_input,
    ask_int,
    ask_multiselect,
    ask_multiselect_interactive,
    ask_secret,
    ask_select,
    ask_select_interactive,
    ask_url,
)

# ── layout ───────────────────────────────────────────────────────────
from .layout import (                              # noqa: F401
    DashboardLayout,
    LiveTable,
    clear_screen,
    columns,
    grid,
    live_dashboard,
    live_table,
    pager,
    scrollable_panel,
    split_horizontal,
    terminal_size,
)

# ── logging ──────────────────────────────────────────────────────────
from .termui_logging import (                      # noqa: F401
    RichHandler,
    capture_logs,
    get_logger,
    set_level,
)

# ── notify ───────────────────────────────────────────────────────────
from .notify import (                              # noqa: F401
    NotifyLevel,
    NotifyQueue,
    notification_history,
    notify,
    replay_notifications,
    sticky_notify,
)

# ── diff ─────────────────────────────────────────────────────────────
from .diff import (                                # noqa: F401
    DiffSummary,
    diff_summary,
    print_diff,
    print_diff_dirs,
    print_diff_files,
)

# ── table_stream ─────────────────────────────────────────────────────
from .table_stream import StreamingTable           # noqa: F401

# ── confirm_panel ────────────────────────────────────────────────────
from .confirm_panel import confirm_action          # noqa: F401

# ── clipboard ────────────────────────────────────────────────────────
from .clipboard import (                           # noqa: F401
    clipboard_available,
    copy_to_clipboard,
    paste_from_clipboard,
)

__version__ = "1.0.0"
__all__ = [
    "DashboardLayout",
    "DiffSummary",
    "LiveTable",
    "NotifyLevel",
    "NotifyQueue",
    "RichHandler",
    "SpinnerGroup",
    "StreamingTable",
    "Theme",
    "ThemeConfig",
    "apply_theme",
    "ask_autocomplete",
    "ask_confirm",
    "ask_date",
    "ask_datetime",
    "ask_directory",
    "ask_editor",
    "ask_email",
    "ask_file",
    "ask_float",
    "ask_form",
    "ask_input",
    "ask_int",
    "ask_multiselect",
    "ask_multiselect_interactive",
    "ask_secret",
    "ask_select",
    "ask_select_interactive",
    "ask_url",
    "capture_logs",
    "clear_screen",
    "clipboard_available",
    "columns",
    "confirm_action",
    "console",
    "console_lock",
    "copy_to_clipboard",
    "current_theme_name",
    "diff_summary",
    "get_console",
    "get_logger",
    "get_theme",
    "grid",
    "is_dumb_terminal",
    "list_themes",
    "live_dashboard",
    "live_table",
    "load_theme",
    "locked_console",
    "notification_history",
    "notify",
    "pager",
    "paste_from_clipboard",
    "print_callout",
    "print_diff",
    "print_diff_dirs",
    "print_diff_files",
    "print_error",
    "print_header",
    "print_info",
    "print_json",
    "print_key_value",
    "print_markdown",
    "print_metric",
    "print_metric_group",
    "print_panel",
    "print_rule",
    "print_status_grid",
    "print_success",
    "print_syntax",
    "print_table",
    "print_text",
    "print_timeline",
    "print_tree",
    "print_warning",
    "progress_bar",
    "progress_map",
    "progress_track",
    "register_theme",
    "replay_notifications",
    "save_theme",
    "scrollable_panel",
    "set_level",
    "spinner",
    "spinner_group",
    "split_horizontal",
    "sticky_notify",
    "terminal_size",
    "theme_context",
]
