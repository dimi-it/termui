"""ui.theme — Centralized style theme with light/dark presets.

Usage
-----
    from ui.theme import apply_theme, Theme

    apply_theme(Theme.DARK)   # default
    apply_theme(Theme.LIGHT)
    apply_theme(Theme.MONOKAI)

Custom themes can be registered and used by name::

    from ui.theme import register_theme, ThemeConfig
    register_theme("ocean", ThemeConfig(success="bold #00bfff"))
    apply_theme("ocean")

A context manager allows temporary theme switching::

    from ui.theme import theme_context, Theme
    with theme_context(Theme.LIGHT):
        print_info("This is light-themed")
    # original theme is restored here
"""

from __future__ import annotations

import json as _json
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Generator

from prompt_toolkit.styles import Style as PTStyle
from rich.theme import Theme as RichTheme

from .console import console


# ── Dataclass that holds every configurable colour ───────────────────

@dataclass
class ThemeConfig:
    """Complete colour / style palette for the UI.

    Parameters
    ----------
    success : str
        Rich style for success messages.
    error : str
        Rich style for error messages.
    warning : str
        Rich style for warning messages.
    info : str
        Rich style for informational messages.
    panel_border : str
        Border style for panels.
    header_border : str
        Border style for headers.
    table_border : str
        Border style for tables.
    table_header : str
        Style for table header cells.
    rule_style : str
        Style for horizontal rules.
    syntax_theme : str
        Pygments theme name for syntax highlighting.
    spinner_style : str
        Style for spinners.
    pt_prompt : str
        prompt_toolkit style for the prompt label.
    pt_input : str
        prompt_toolkit style for user input text.
    pt_selected : str
        prompt_toolkit style for selected items.
    pt_checked : str
        prompt_toolkit style for checked items.
    pt_error : str
        prompt_toolkit style for error messages.
    extra : dict[str, str]
        Extra tokens used in ask_form / ask_autocomplete.

    Examples
    --------
    >>> cfg = ThemeConfig(success="bold #00ff00")
    >>> d = cfg.to_dict()
    >>> cfg2 = ThemeConfig.from_dict(d)
    """

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

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        """Convert this config to a plain dictionary.

        Returns
        -------
        dict[str, object]
            JSON-serializable dictionary of all fields.

        Examples
        --------
        >>> ThemeConfig().to_dict()["success"]
        'bold green'
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "ThemeConfig":
        """Create a ``ThemeConfig`` from a dictionary.

        Parameters
        ----------
        d : dict[str, object]
            Dictionary with field names as keys.

        Returns
        -------
        ThemeConfig
            New instance populated from *d*.

        Examples
        --------
        >>> ThemeConfig.from_dict({"success": "bold blue"}).success
        'bold blue'
        """
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)  # type: ignore[arg-type]


# ── Built-in presets ─────────────────────────────────────────────────

class Theme(Enum):
    """Built-in theme names."""

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

# ── Custom theme registry ────────────────────────────────────────────

_custom_themes: dict[str, ThemeConfig] = {}

# ── Active theme (module-level singleton) ────────────────────────────

_active: ThemeConfig = _PRESETS[Theme.DARK]
_active_name: str = Theme.DARK.value


def _push_rich_theme(cfg: ThemeConfig) -> None:
    """Push the active palette onto the shared rich console."""
    rich_theme = RichTheme({
        "success": cfg.success,
        "error": cfg.error,
        "warning": cfg.warning,
        "info": cfg.info,
    })
    console.push_theme(rich_theme)


# ── Public API ───────────────────────────────────────────────────────

def register_theme(name: str, config: ThemeConfig) -> None:
    """Register a custom named theme.

    Parameters
    ----------
    name : str
        Case-sensitive name for the theme.
    config : ThemeConfig
        The colour/style configuration.

    Raises
    ------
    ValueError
        If *name* collides with a built-in ``Theme`` enum value.

    Examples
    --------
    >>> register_theme("ocean", ThemeConfig(info="bold #00bfff"))
    >>> apply_theme("ocean")
    """
    builtin_names = {t.value for t in Theme}
    if name in builtin_names:
        raise ValueError(
            f"Cannot override built-in theme {name!r}. "
            "Use a different name for custom themes."
        )
    _custom_themes[name] = config


def get_theme(name: str) -> ThemeConfig:
    """Return a theme config by name.

    Parameters
    ----------
    name : str
        Built-in theme value (e.g. ``"dark"``) or a registered custom name.

    Returns
    -------
    ThemeConfig

    Raises
    ------
    KeyError
        If no theme with *name* exists.

    Examples
    --------
    >>> get_theme("dark").success
    'bold green'
    """
    # Check custom first, then built-in
    if name in _custom_themes:
        return _custom_themes[name]
    for t in Theme:
        if t.value == name:
            return _PRESETS[t]
    raise KeyError(f"Unknown theme: {name!r}")


def apply_theme(theme: Theme | ThemeConfig | str) -> None:
    """Switch the global theme.

    Accepts a ``Theme`` enum, a ``ThemeConfig`` instance, or a string name
    (built-in or custom-registered).

    Parameters
    ----------
    theme : Theme | ThemeConfig | str
        The theme to activate.

    Raises
    ------
    TypeError
        If *theme* is not a recognised type.
    KeyError
        If a string name is not found.

    Examples
    --------
    >>> apply_theme(Theme.MONOKAI)
    >>> apply_theme("dark")
    >>> apply_theme(ThemeConfig(success="bold magenta"))
    """
    global _active, _active_name
    if isinstance(theme, Theme):
        _active = _PRESETS[theme]
        _active_name = theme.value
    elif isinstance(theme, str):
        _active = get_theme(theme)
        _active_name = theme
    elif isinstance(theme, ThemeConfig):
        _active = theme
        _active_name = "<custom>"
    else:
        raise TypeError(f"Expected Theme, ThemeConfig, or str, got {type(theme)}")

    _push_rich_theme(_active)


def current() -> ThemeConfig:
    """Return the active ``ThemeConfig``."""
    return _active


def current_theme_name() -> str:
    """Return the name of the currently active theme.

    Returns
    -------
    str
        A built-in name like ``"dark"`` or a custom name, or ``"<custom>"``
        if the theme was applied via a raw ``ThemeConfig``.

    Examples
    --------
    >>> apply_theme(Theme.DARK)
    >>> current_theme_name()
    'dark'
    """
    return _active_name


def list_themes() -> list[str]:
    """Return all available theme names (built-in + custom-registered).

    Returns
    -------
    list[str]
        Sorted list of theme names.

    Examples
    --------
    >>> "dark" in list_themes()
    True
    """
    names = [t.value for t in Theme] + list(_custom_themes.keys())
    return sorted(names)


# ── Theme context manager ────────────────────────────────────────────

@contextmanager
def theme_context(theme: Theme | ThemeConfig | str) -> Generator[None, None, None]:
    """Temporarily switch the theme within a ``with`` block.

    The previous theme is restored on exit (including on exceptions).

    Parameters
    ----------
    theme : Theme | ThemeConfig | str
        The theme to use inside the block.

    Examples
    --------
    >>> with theme_context(Theme.LIGHT):
    ...     print_info("light themed")
    """
    global _active, _active_name
    prev_config = _active
    prev_name = _active_name
    try:
        apply_theme(theme)
        yield
    finally:
        _active = prev_config
        _active_name = prev_name
        _push_rich_theme(_active)


# ── Persistence helpers ──────────────────────────────────────────────

def save_theme(config: ThemeConfig, path: Path | str) -> None:
    """Save a ``ThemeConfig`` to a JSON file.

    Parameters
    ----------
    config : ThemeConfig
        Theme to serialise.
    path : Path | str
        Destination file path.

    Examples
    --------
    >>> save_theme(ThemeConfig(), "/tmp/my_theme.json")
    """
    p = Path(path)
    p.write_text(_json.dumps(config.to_dict(), indent=2), encoding="utf-8")


def load_theme(path: Path | str) -> ThemeConfig:
    """Load a ``ThemeConfig`` from a JSON file.

    Parameters
    ----------
    path : Path | str
        Source file path.

    Returns
    -------
    ThemeConfig

    Examples
    --------
    >>> cfg = load_theme("/tmp/my_theme.json")
    """
    p = Path(path)
    data = _json.loads(p.read_text(encoding="utf-8"))
    return ThemeConfig.from_dict(data)


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
