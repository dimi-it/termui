"""ui.theme — Centralized style theme with light/dark presets.

Usage
-----
    from ui.theme import apply_theme, Theme

    apply_theme(Theme.DARK)   # default
    apply_theme(Theme.LIGHT)
    apply_theme(Theme.MONOKAI)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from prompt_toolkit.styles import Style as PTStyle
from rich.theme import Theme as RichTheme

from .console import console


# ── Dataclass that holds every configurable colour ───────────────────

@dataclass
class ThemeConfig:
    # rich styles
    success: str = "bold green"
    error: str = "bold red"
    warning: str = "bold yellow"
    info: str = "bold cyan"
    panel_border: str = "cyan"
    header_border: str = "magenta"
    table_border: str = "cyan"
    table_header: str = "bold cyan"
    rule_style: str = "dim cyan"
    syntax_theme: str = "monokai"
    spinner_style: str = "cyan"
    # prompt_toolkit styles (css-like strings)
    pt_prompt: str = "bold cyan"
    pt_input: str = "yellow"
    pt_selected: str = "reverse cyan"
    pt_checked: str = "bold green"
    pt_error: str = "bold red"
    # extra tokens used in ask_form / ask_autocomplete
    extra: dict[str, str] = field(default_factory=dict)


# ── Built-in presets ─────────────────────────────────────────────────

class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    MONOKAI = "monokai"
    SOLARIZED = "solarized"
    PLAIN = "plain"


_PRESETS: dict[Theme, ThemeConfig] = {
    Theme.DARK: ThemeConfig(),  # defaults are already dark-friendly
    Theme.LIGHT: ThemeConfig(
        success="bold dark_green",
        error="bold dark_red",
        warning="bold dark_goldenrod",
        info="bold blue",
        panel_border="blue",
        header_border="purple",
        table_border="blue",
        table_header="bold blue",
        rule_style="dim blue",
        syntax_theme="friendly",
        spinner_style="blue",
        pt_prompt="bold blue",
        pt_input="black",
        pt_selected="reverse blue",
    ),
    Theme.MONOKAI: ThemeConfig(
        success="bold #a6e22e",
        error="bold #f92672",
        warning="bold #e6db74",
        info="bold #66d9ef",
        panel_border="#66d9ef",
        header_border="#ae81ff",
        table_border="#66d9ef",
        table_header="bold #66d9ef",
        rule_style="dim #75715e",
        syntax_theme="monokai",
        spinner_style="#66d9ef",
        pt_prompt="bold #66d9ef",
        pt_input="#f8f8f2",
        pt_selected="reverse #66d9ef",
    ),
    Theme.SOLARIZED: ThemeConfig(
        success="bold #859900",
        error="bold #dc322f",
        warning="bold #b58900",
        info="bold #268bd2",
        panel_border="#268bd2",
        header_border="#6c71c4",
        table_border="#268bd2",
        table_header="bold #268bd2",
        rule_style="dim #657b83",
        syntax_theme="solarized-dark",
        spinner_style="#268bd2",
        pt_prompt="bold #268bd2",
        pt_input="#fdf6e3",
        pt_selected="reverse #268bd2",
    ),
    Theme.PLAIN: ThemeConfig(
        success="",
        error="",
        warning="",
        info="",
        panel_border="",
        header_border="",
        table_border="",
        table_header="bold",
        rule_style="dim",
        syntax_theme="default",
        spinner_style="",
        pt_prompt="bold",
        pt_input="",
        pt_selected="reverse",
    ),
}

# ── Active theme (module-level singleton) ────────────────────────────

_active: ThemeConfig = _PRESETS[Theme.DARK]


def apply_theme(theme: Theme | ThemeConfig) -> None:
    """Switch the global theme.  Accepts a ``Theme`` enum or a custom
    ``ThemeConfig`` instance."""
    global _active
    if isinstance(theme, Theme):
        _active = _PRESETS[theme]
    elif isinstance(theme, ThemeConfig):
        _active = theme
    else:
        raise TypeError(f"Expected Theme or ThemeConfig, got {type(theme)}")

    # Push the new palette onto the shared console
    rich_theme = RichTheme({
        "success": _active.success,
        "error": _active.error,
        "warning": _active.warning,
        "info": _active.info,
    })
    console.push_theme(rich_theme)


def current() -> ThemeConfig:
    """Return the active ``ThemeConfig``."""
    return _active


def pt_style() -> PTStyle:
    """Return a ``prompt_toolkit`` Style built from the active theme."""
    t = _active
    mapping = {
        "prompt": t.pt_prompt,
        "": t.pt_input,
        "selected": t.pt_selected,
        "checked": t.pt_checked,
        "error": t.pt_error,
    }
    mapping.update(t.extra)
    return PTStyle.from_dict(mapping)
