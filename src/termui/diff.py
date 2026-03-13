"""ui.diff — Diff rendering helpers.

Usage
-----
    from ui.diff import print_diff, print_diff_files

    print_diff(old_text, new_text, title_old="v1.py", title_new="v2.py")
    print_diff_files("/path/to/a.py", "/path/to/b.py")

Renders using ``rich.syntax`` with a unified diff so the output is
syntax-coloured and patch-style simultaneously.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Optional

from rich.columns import Columns
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from .console import console
from . import theme as _theme


def _unified_diff(
    old: str,
    new: str,
    from_file: str = "old",
    to_file: str = "new",
    context_lines: int = 3,
) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            old_lines, new_lines,
            fromfile=from_file, tofile=to_file,
            n=context_lines,
        )
    )


def print_diff(
    old: str,
    new: str,
    *,
    title_old: str = "Before",
    title_new: str = "After",
    language: str = "diff",
    mode: str = "unified",
    context_lines: int = 3,
) -> None:
    """Render a diff between two strings.

    Parameters
    ----------
    old:           Original text.
    new:           Modified text.
    title_old:     Label for the old version.
    title_new:     Label for the new version.
    language:      Pygments language for syntax highlighting.
                   ``"diff"`` gives standard patch colouring.
                   Use ``"python"``, ``"javascript"``, etc. for richer
                   highlighting of language-aware diffs.
    mode:          ``"unified"`` (default) – unified diff output.
                   ``"side-by-side"`` – original on left, new on right.
    context_lines: Number of unchanged context lines around each change.
    """
    t = _theme.current()

    if mode == "side-by-side":
        old_panel = Panel(
            Syntax(old, language, theme=t.syntax_theme, line_numbers=True),
            title=title_old,
            border_style=t.panel_border,
        )
        new_panel = Panel(
            Syntax(new, language, theme=t.syntax_theme, line_numbers=True),
            title=title_new,
            border_style=t.panel_border,
        )
        console.print(Columns([old_panel, new_panel], equal=True, expand=True))
        return

    # unified
    patch = _unified_diff(old, new, from_file=title_old, to_file=title_new,
                          context_lines=context_lines)
    if not patch:
        console.print("[dim]No differences found.[/dim]")
        return

    syn = Syntax(patch, "diff", theme=t.syntax_theme, line_numbers=False)
    console.print(
        Panel(syn, title=f"Diff: {title_old} → {title_new}", border_style=t.panel_border)
    )


def print_diff_files(
    path_old: str | Path,
    path_new: str | Path,
    *,
    language: str = "diff",
    mode: str = "unified",
    context_lines: int = 3,
    encoding: str = "utf-8",
) -> None:
    """Read two files from disk and call :func:`print_diff`.

    Parameters
    ----------
    path_old:      Path to the original file.
    path_new:      Path to the modified file.
    language:      Pygments language identifier.
    mode:          ``"unified"`` or ``"side-by-side"``.
    context_lines: Context lines in unified mode.
    encoding:      File encoding (default ``"utf-8"``).
    """
    p_old = Path(path_old)
    p_new = Path(path_new)
    old_text = p_old.read_text(encoding=encoding)
    new_text = p_new.read_text(encoding=encoding)
    print_diff(
        old_text, new_text,
        title_old=str(p_old),
        title_new=str(p_new),
        language=language,
        mode=mode,
        context_lines=context_lines,
    )
