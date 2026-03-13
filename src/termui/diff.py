"""ui.diff — Diff rendering helpers.

Usage
-----
    from ui.diff import print_diff, print_diff_files

    print_diff(old_text, new_text, title_old="v1.py", title_new="v2.py")
    print_diff_files("/path/to/a.py", "/path/to/b.py")

Character-level highlighting::

    print_diff("hello world", "hello there", mode="side-by-side",
               char_highlight=True)

Diff summary (counts only)::

    summary = diff_summary("old", "new")
    print(summary.added, summary.removed)

Directory diffs::

    print_diff_dirs("dir_a", "dir_b")

Renders using ``rich.syntax`` with a unified diff so the output is
syntax-coloured and patch-style simultaneously.
"""

from __future__ import annotations

import difflib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.columns import Columns
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .console import console, console_lock
from . import theme as _theme


# ── Diff summary dataclass ───────────────────────────────────────────

@dataclass(frozen=True)
class DiffSummary:
    """Statistical summary of a diff between two strings.

    Attributes
    ----------
    added : int
        Number of added lines.
    removed : int
        Number of removed lines.
    changed : int
        Number of changed (replaced) lines.
    unchanged : int
        Number of unchanged lines.
    """

    added: int
    removed: int
    changed: int
    unchanged: int


def diff_summary(
    old: str,
    new: str,
    *,
    ignore_whitespace: bool = False,
) -> DiffSummary:
    """Compute diff statistics without rendering.

    Parameters
    ----------
    old : str
        Original text.
    new : str
        Modified text.
    ignore_whitespace : bool
        Strip trailing whitespace from each line before comparing.

    Returns
    -------
    DiffSummary

    Examples
    --------
    >>> s = diff_summary("a\\nb\\nc", "a\\nx\\nc")
    >>> s.changed
    1
    """
    old_lines = _prep_lines(old, ignore_whitespace)
    new_lines = _prep_lines(new, ignore_whitespace)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    added = removed = changed = unchanged = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            unchanged += i2 - i1
        elif tag == "replace":
            changed += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "insert":
            added += j2 - j1
    return DiffSummary(added=added, removed=removed, changed=changed, unchanged=unchanged)


def _prep_lines(text: str, strip_ws: bool) -> list[str]:
    lines = text.splitlines()
    if strip_ws:
        lines = [l.rstrip() for l in lines]
    return lines


# ── Internal helpers ─────────────────────────────────────────────────

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


def _char_highlight_pair(old_line: str, new_line: str) -> tuple[Text, Text]:
    """Return a (old_text, new_text) pair with character-level highlighting."""
    sm = difflib.SequenceMatcher(None, old_line, new_line)
    old_text = Text()
    new_text = Text()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            old_text.append(old_line[i1:i2])
            new_text.append(new_line[j1:j2])
        elif tag == "replace":
            old_text.append(old_line[i1:i2], style="bold red on #3d0000")
            new_text.append(new_line[j1:j2], style="bold green on #003d00")
        elif tag == "delete":
            old_text.append(old_line[i1:i2], style="bold red on #3d0000")
        elif tag == "insert":
            new_text.append(new_line[j1:j2], style="bold green on #003d00")
    return old_text, new_text


def _side_by_side_table(
    old: str, new: str,
    title_old: str, title_new: str,
    char_highlight: bool = False,
) -> Table:
    """Build a rich Table with side-by-side line diff."""
    t = _theme.current()
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    table = Table(
        title="Side-by-Side Diff",
        show_header=True,
        border_style=t.table_border,
        header_style=t.table_header,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column(title_old, ratio=1)
    table.add_column("#", style="dim", width=4)
    table.add_column(title_new, ratio=1)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                table.add_row(str(i + 1), old_lines[i], str(j + 1), new_lines[j])
        elif tag == "replace":
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                ol = old_lines[i1 + k] if k < (i2 - i1) else ""
                nl = new_lines[j1 + k] if k < (j2 - j1) else ""
                onum = str(i1 + k + 1) if k < (i2 - i1) else ""
                nnum = str(j1 + k + 1) if k < (j2 - j1) else ""
                if char_highlight and ol and nl:
                    ot, nt = _char_highlight_pair(ol, nl)
                else:
                    ot = Text(ol, style="red")
                    nt = Text(nl, style="green")
                table.add_row(onum, ot, nnum, nt)
        elif tag == "delete":
            for i in range(i1, i2):
                table.add_row(str(i + 1), Text(old_lines[i], style="red"), "", "")
        elif tag == "insert":
            for j in range(j1, j2):
                table.add_row("", "", str(j + 1), Text(new_lines[j], style="green"))
    return table


# ── Public API ───────────────────────────────────────────────────────

def print_diff(
    old: str,
    new: str,
    *,
    title_old: str = "Before",
    title_new: str = "After",
    language: str = "diff",
    mode: str = "unified",
    context_lines: int = 3,
    char_highlight: bool = False,
    ignore_whitespace: bool = False,
) -> None:
    """Render a diff between two strings.

    Parameters
    ----------
    old:              Original text.
    new:              Modified text.
    title_old:        Label for the old version.
    title_new:        Label for the new version.
    language:         Pygments language for syntax highlighting.
                      ``"diff"`` gives standard patch colouring.
                      Use ``"python"``, ``"javascript"``, etc. for richer
                      highlighting of language-aware diffs.
    mode:             ``"unified"`` (default) – unified diff output.
                      ``"side-by-side"`` – original on left, new on right.
    context_lines:    Number of unchanged context lines around each change.
    char_highlight:   Enable character-level diff highlighting in
                      ``side-by-side`` mode.
    ignore_whitespace: Strip trailing whitespace before comparing.
    """
    if ignore_whitespace:
        old = "\n".join(l.rstrip() for l in old.splitlines())
        new = "\n".join(l.rstrip() for l in new.splitlines())

    t = _theme.current()

    if mode not in ("unified", "side-by-side"):
        raise ValueError(f"Unknown diff mode: {mode!r}")

    if mode == "side-by-side":
        if char_highlight:
            table = _side_by_side_table(old, new, title_old, title_new, char_highlight=True)
            with console_lock:
                console.print(table)
        else:
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
            with console_lock:
                console.print(Columns([old_panel, new_panel], equal=True, expand=True))
        return

    # unified
    patch = _unified_diff(old, new, from_file=title_old, to_file=title_new,
                          context_lines=context_lines)
    if not patch:
        with console_lock:
            console.print("[dim]No differences found.[/dim]")
        return

    syn = Syntax(patch, "diff", theme=t.syntax_theme, line_numbers=False)
    with console_lock:
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
    char_highlight: bool = False,
    ignore_whitespace: bool = False,
) -> None:
    """Read two files from disk and call :func:`print_diff`.

    Parameters
    ----------
    path_old:          Path to the original file.
    path_new:          Path to the modified file.
    language:          Pygments language identifier.
    mode:              ``"unified"`` or ``"side-by-side"``.
    context_lines:     Context lines in unified mode.
    encoding:          File encoding (default ``"utf-8"``).
    char_highlight:    Character-level highlighting for ``side-by-side``.
    ignore_whitespace: Ignore trailing whitespace differences.
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
        char_highlight=char_highlight,
        ignore_whitespace=ignore_whitespace,
    )


def print_diff_dirs(
    dir_a: str | Path,
    dir_b: str | Path,
    *,
    extensions: list[str] | None = None,
    mode: str = "unified",
    context_lines: int = 3,
    ignore_whitespace: bool = False,
) -> None:
    """Compare all matching files in two directories.

    Only files present in **both** directories are compared (by relative
    path).  Files unique to one side are listed separately.

    Parameters
    ----------
    dir_a : str | Path
        First directory.
    dir_b : str | Path
        Second directory.
    extensions : list[str] | None
        If given, only compare files whose suffix is in this list
        (e.g. ``[".py", ".txt"]``).
    mode : str
        ``"unified"`` or ``"side-by-side"``.
    context_lines : int
        Context lines for unified diffs.
    ignore_whitespace : bool
        Ignore trailing whitespace.

    Examples
    --------
    >>> print_diff_dirs("project_v1", "project_v2", extensions=[".py"])
    """
    pa = Path(dir_a)
    pb = Path(dir_b)

    def _gather(root: Path) -> set[str]:
        result: set[str] = set()
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                full = Path(dirpath) / fn
                rel = str(full.relative_to(root))
                if extensions is None or full.suffix in extensions:
                    result.add(rel)
        return result

    files_a = _gather(pa)
    files_b = _gather(pb)
    common = sorted(files_a & files_b)
    only_a = sorted(files_a - files_b)
    only_b = sorted(files_b - files_a)

    with console_lock:
        if only_a:
            console.print(f"[red]Only in {dir_a}:[/red]")
            for f in only_a:
                console.print(f"  [red]- {f}[/red]")
        if only_b:
            console.print(f"[green]Only in {dir_b}:[/green]")
            for f in only_b:
                console.print(f"  [green]+ {f}[/green]")

    for rel in common:
        a_text = (pa / rel).read_text(encoding="utf-8")
        b_text = (pb / rel).read_text(encoding="utf-8")
        if a_text != b_text:
            with console_lock:
                console.print(f"\n[bold]--- {rel} ---[/bold]")
            print_diff(
                a_text, b_text,
                title_old=f"{dir_a}/{rel}",
                title_new=f"{dir_b}/{rel}",
                mode=mode,
                context_lines=context_lines,
                ignore_whitespace=ignore_whitespace,
            )
