"""ui.clipboard — Clipboard utilities with graceful degradation.

Requires the optional ``pyperclip`` dependency.  Install via::

    pip install termui[clipboard]

All functions raise a clear ``ImportError`` with install instructions if
``pyperclip`` is not available.

Usage
-----
    from ui.clipboard import copy_to_clipboard, paste_from_clipboard

    copy_to_clipboard("Hello, world!")
    text = paste_from_clipboard()
"""

from __future__ import annotations

from typing import Optional

from .console import console, console_lock

_INSTALL_HINT = (
    "Clipboard support requires the 'pyperclip' package.\n"
    "Install it with:  pip install termui[clipboard]"
)


def _get_pyperclip() -> object:
    """Import and return the ``pyperclip`` module, or raise."""
    try:
        import pyperclip  # type: ignore[import-untyped]
        return pyperclip
    except ImportError:
        raise ImportError(_INSTALL_HINT) from None


def copy_to_clipboard(text: str, *, notify: bool = True) -> None:
    """Copy *text* to the system clipboard.

    Parameters
    ----------
    text : str
        The string to copy.
    notify : bool
        If ``True``, print a confirmation message to the console.

    Raises
    ------
    ImportError
        If ``pyperclip`` is not installed.

    Examples
    --------
    >>> copy_to_clipboard("Hello!")
    """
    pyperclip = _get_pyperclip()
    pyperclip.copy(text)  # type: ignore[union-attr]
    if notify:
        preview = text[:40] + ("…" if len(text) > 40 else "")
        with console_lock:
            console.print(f"[dim]📋 Copied to clipboard: {preview!r}[/dim]")


def paste_from_clipboard() -> str:
    """Return the current clipboard contents.

    Returns
    -------
    str
        The clipboard text.

    Raises
    ------
    ImportError
        If ``pyperclip`` is not installed.

    Examples
    --------
    >>> text = paste_from_clipboard()
    """
    pyperclip = _get_pyperclip()
    return str(pyperclip.paste())  # type: ignore[union-attr]


def clipboard_available() -> bool:
    """Check whether clipboard functionality is available.

    Returns
    -------
    bool
        ``True`` if ``pyperclip`` is importable, ``False`` otherwise.

    Examples
    --------
    >>> if clipboard_available():
    ...     copy_to_clipboard("safe to call")
    """
    try:
        import pyperclip  # type: ignore[import-untyped]  # noqa: F401
        return True
    except ImportError:
        return False
