"""termui — A rich terminal UI library for AI agent interactions.

Modules
-------
console     Shared ``rich`` Console singleton and low-level print helpers.
output      High-level output: panels, tables, trees, progress, markdown …
input       Prompt-toolkit input helpers: text, confirm, select, file, form …
layout      Multi-column layouts, grids, rule separators, live dashboards.
theme       Centralized colour / style theme with light/dark switching.
logging     Drop-in structured log handler that renders through rich.
notify      Desktop-style notification toasts inside the terminal.
diff        Side-by-side and inline diff rendering.
"""

from .console import console, get_console          # noqa: F401
from .theme import Theme, apply_theme              # noqa: F401

from .output import (                              # noqa: F401
    print_text,
    print_panel,
    print_markdown,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_table,
    print_tree,
    print_json,
    print_syntax,
    print_rule,
    print_key_value,
    spinner,
    progress_bar,
    progress_track,
)

from .input import (                               # noqa: F401
    ask_input,
    ask_confirm,
    ask_file,
    ask_directory,
    ask_select,
    ask_multiselect,
    ask_secret,
    ask_int,
    ask_float,
    ask_form,
    ask_editor,
    ask_autocomplete,
)

from .layout import (                              # noqa: F401
    columns,
    live_dashboard,
    clear_screen,
    print_header,
)

from .termui_logging import (                             # noqa: F401
    get_logger,
    RichHandler,
)

from .notify import notify                        # noqa: F401
from .diff import print_diff, print_diff_files   # noqa: F401

__version__ = "1.0.0"
__all__ = [
    # console
    "console", "get_console",
    # theme
    "Theme", "apply_theme",
    # output
    "print_text", "print_panel", "print_markdown", "print_success",
    "print_error", "print_warning", "print_info", "print_table",
    "print_tree", "print_json", "print_syntax", "print_rule",
    "print_key_value", "spinner", "progress_bar", "progress_track",
    # input
    "ask_input", "ask_confirm", "ask_file", "ask_directory",
    "ask_select", "ask_multiselect", "ask_secret", "ask_int",
    "ask_float", "ask_form", "ask_editor", "ask_autocomplete",
    # layout
    "columns", "live_dashboard", "clear_screen", "print_header",
    # logging
    "get_logger", "RichHandler",
    # notify
    "notify",
    # diff
    "print_diff", "print_diff_files",
]
