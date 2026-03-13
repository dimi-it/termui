"""ui.input — User-input helpers built on ``prompt_toolkit``.

All prompts use the active theme and share a single ``PromptSession``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    Completer,
    FuzzyCompleter,
    PathCompleter,
    WordCompleter,
)
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.validation import ValidationError, Validator

from . import theme as _theme
from .output import print_error, print_table

T = TypeVar("T")

# ── Shared PromptSession ─────────────────────────────────────────────

_session: PromptSession | None = None


def _get_session() -> PromptSession:
    global _session
    if _session is None:
        _session = PromptSession(style=_theme.pt_style())
    return _session


def _prompt(label: str, **kwargs: Any) -> str:
    """Internal wrapper: rebuild session style on every call (theme may change)."""
    session = _get_session()
    session.style = _theme.pt_style()
    return session.prompt(
        FormattedText([("class:prompt", f"{label} ❯ ")]),
        **kwargs,
    ).strip()


# ── Validators ───────────────────────────────────────────────────────

class _RangeValidator(Validator):
    def __init__(self, lo: float | None, hi: float | None, cast: type) -> None:
        self._lo, self._hi, self._cast = lo, hi, cast

    def validate(self, document: Any) -> None:
        text = document.text.strip()
        try:
            v = self._cast(text)
        except ValueError:
            raise ValidationError(message=f"Enter a valid {self._cast.__name__}.")
        if self._lo is not None and v < self._lo:
            raise ValidationError(message=f"Must be ≥ {self._lo}.")
        if self._hi is not None and v > self._hi:
            raise ValidationError(message=f"Must be ≤ {self._hi}.")


class _RegexValidator(Validator):
    def __init__(self, pattern: str, message: str) -> None:
        import re
        self._re = re.compile(pattern)
        self._message = message

    def validate(self, document: Any) -> None:
        if not self._re.fullmatch(document.text.strip()):
            raise ValidationError(message=self._message)


# ── Text input ───────────────────────────────────────────────────────

def ask_input(
    prompt_text: str,
    *,
    default: str = "",
    placeholder: str = "",
    validator: Optional[Callable[[str], bool]] = None,
    error_message: str = "Invalid input.",
    allow_empty: bool = False,
) -> str:
    """General-purpose text prompt.

    Parameters
    ----------
    prompt_text:   Label shown before the ``❯`` cursor.
    default:       Pre-filled default value (user can clear it).
    placeholder:   Ghost text visible when the field is empty.
    validator:     Optional callable; return ``True`` if valid.
    error_message: Shown when *validator* returns ``False``.
    allow_empty:   If ``False``, an empty answer is rejected.
    """
    while True:
        result = _prompt(prompt_text, default=default)
        if not result and not allow_empty:
            print_error("Input cannot be empty.")
            continue
        if validator and not validator(result):
            print_error(error_message)
            continue
        return result


def ask_secret(
    prompt_text: str,
    *,
    confirm: bool = False,
    confirm_prompt: str = "Confirm",
) -> str:
    """Password / secret prompt that masks input.

    Parameters
    ----------
    prompt_text:    Label for the first prompt.
    confirm:        If ``True``, ask the user to re-enter for verification.
    confirm_prompt: Label for the confirmation prompt.
    """
    while True:
        value = _get_session().prompt(
            FormattedText([("class:prompt", f"{prompt_text} ❯ ")]),
            is_password=True,
        ).strip()
        if not confirm:
            return value
        confirm_value = _get_session().prompt(
            FormattedText([("class:prompt", f"{confirm_prompt} ❯ ")]),
            is_password=True,
        ).strip()
        if value == confirm_value:
            return value
        print_error("Values do not match. Try again.")


# ── Numeric input ────────────────────────────────────────────────────

def ask_int(
    prompt_text: str,
    *,
    default: Optional[int] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    """Integer prompt with optional range validation.

    Parameters
    ----------
    prompt_text: Label shown before the cursor.
    default:     Pre-filled integer default.
    min_value:   Inclusive lower bound.
    max_value:   Inclusive upper bound.
    """
    validator = _RangeValidator(min_value, max_value, int)
    label = prompt_text
    if min_value is not None or max_value is not None:
        bounds = f"{min_value or '−∞'} – {max_value or '+∞'}"
        label = f"{prompt_text} [{bounds}]"
    while True:
        raw = _prompt(label, default=str(default) if default is not None else "")
        try:
            validator.validate(type("D", (), {"text": raw})())
            return int(raw)
        except ValidationError as exc:
            print_error(str(exc.message))


def ask_float(
    prompt_text: str,
    *,
    default: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
) -> float:
    """Float prompt with optional range validation."""
    validator = _RangeValidator(min_value, max_value, float)
    label = prompt_text
    while True:
        raw = _prompt(label, default=str(default) if default is not None else "")
        try:
            validator.validate(type("D", (), {"text": raw})())
            return float(raw)
        except ValidationError as exc:
            print_error(str(exc.message))


# ── Confirmation ─────────────────────────────────────────────────────

def ask_confirm(prompt_text: str, *, default: bool = True) -> bool:
    """Yes/No confirmation prompt.

    Parameters
    ----------
    prompt_text: Question to display.
    default:     Value returned when the user presses Enter without typing.
    """
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        raw = _prompt(f"{prompt_text} {hint}").lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print_error("Please type 'y' or 'n'.")


# ── File / directory ─────────────────────────────────────────────────

def ask_file(
    prompt_text: str,
    *,
    extensions: Optional[List[str]] = None,
    must_exist: bool = True,
) -> str:
    """File-path prompt with filesystem tab-completion.

    Parameters
    ----------
    prompt_text: Label shown before the cursor.
    extensions:  Allowed extensions, e.g. ``[".py", ".txt"]``.
    must_exist:  When ``True``, rejects paths that do not exist on disk.
    """
    completer = PathCompleter(only_directories=False)
    while True:
        raw = _prompt(prompt_text, completer=completer)
        if not raw:
            print_error("No path entered.")
            continue
        resolved = str(Path(os.path.expanduser(raw)).resolve())
        if must_exist and not os.path.isfile(resolved):
            print_error(f"File not found: {resolved}")
            continue
        if extensions and not any(resolved.lower().endswith(e.lower()) for e in extensions):
            print_error(f"Allowed extensions: {', '.join(extensions)}")
            continue
        return resolved


def ask_directory(
    prompt_text: str,
    *,
    must_exist: bool = True,
    create_if_missing: bool = False,
) -> str:
    """Directory-path prompt with tab-completion.

    Parameters
    ----------
    prompt_text:       Label shown before the cursor.
    must_exist:        Reject paths that do not exist.
    create_if_missing: Create the directory if it is absent (overrides *must_exist*).
    """
    completer = PathCompleter(only_directories=True)
    while True:
        raw = _prompt(prompt_text, completer=completer)
        if not raw:
            print_error("No path entered.")
            continue
        resolved = str(Path(os.path.expanduser(raw)).resolve())
        if create_if_missing and not os.path.isdir(resolved):
            os.makedirs(resolved, exist_ok=True)
            return resolved
        if must_exist and not os.path.isdir(resolved):
            print_error(f"Directory not found: {resolved}")
            continue
        return resolved


# ── Single / multi select ────────────────────────────────────────────

def ask_select(
    prompt_text: str,
    options: List[str],
    *,
    default: Optional[int] = None,
) -> str:
    """Numbered single-choice selection.

    Parameters
    ----------
    prompt_text: Question displayed above the list.
    options:     List of choice strings.
    default:     1-based index of the pre-selected choice.
    """
    if not options:
        raise ValueError("options must not be empty")
    print_table(
        ["#", "Option"],
        [(str(i), opt) for i, opt in enumerate(options, 1)],
        title=prompt_text,
    )
    hint = f" (default: {default})" if default is not None else ""
    while True:
        raw = _prompt(f"Enter number{hint}", default=str(default) if default else "")
        if not raw.isdigit():
            print_error("Enter a valid number.")
            continue
        idx = int(raw)
        if not (1 <= idx <= len(options)):
            print_error(f"Choose between 1 and {len(options)}.")
            continue
        return options[idx - 1]


def ask_multiselect(
    prompt_text: str,
    options: List[str],
    *,
    min_choices: int = 1,
    max_choices: Optional[int] = None,
) -> List[str]:
    """Numbered multi-choice selection.

    The user enters comma-separated indices, e.g. ``1,3,4``.

    Parameters
    ----------
    prompt_text:  Question displayed above the list.
    options:      List of choice strings.
    min_choices:  Minimum required selections.
    max_choices:  Maximum allowed selections (``None`` = unlimited).
    """
    if not options:
        raise ValueError("options must not be empty")
    print_table(
        ["#", "Option"],
        [(str(i), opt) for i, opt in enumerate(options, 1)],
        title=prompt_text,
    )
    hint = f"min {min_choices}"
    if max_choices:
        hint += f", max {max_choices}"
    while True:
        raw = _prompt(f"Enter numbers separated by commas ({hint})")
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not all(p.isdigit() for p in parts):
            print_error("Use comma-separated numbers only.")
            continue
        indices = [int(p) for p in parts]
        if not all(1 <= i <= len(options) for i in indices):
            print_error(f"All numbers must be between 1 and {len(options)}.")
            continue
        if len(indices) < min_choices:
            print_error(f"Select at least {min_choices} option(s).")
            continue
        if max_choices and len(indices) > max_choices:
            print_error(f"Select at most {max_choices} option(s).")
            continue
        return [options[i - 1] for i in indices]


# ── Autocomplete ─────────────────────────────────────────────────────

def ask_autocomplete(
    prompt_text: str,
    completions: List[str],
    *,
    fuzzy: bool = True,
    allow_free_text: bool = False,
) -> str:
    """Text prompt with word/fuzzy autocomplete from a list.

    Parameters
    ----------
    prompt_text:    Label shown before the cursor.
    completions:    List of suggested completions.
    fuzzy:          Enable fuzzy matching (e.g. 'pthon' → 'python').
    allow_free_text: Accept answers that are not in *completions*.
    """
    base: Completer = WordCompleter(completions, ignore_case=True)
    completer: Completer = FuzzyCompleter(base) if fuzzy else base
    while True:
        result = _prompt(prompt_text, completer=completer)
        if not result:
            print_error("Input cannot be empty.")
            continue
        if not allow_free_text and result not in completions:
            print_error(f"Choose one of: {', '.join(completions)}")
            continue
        return result


# ── External editor ──────────────────────────────────────────────────

def ask_editor(
    prompt_text: str = "Opening editor…",
    *,
    initial_text: str = "",
    extension: str = ".txt",
    editor: Optional[str] = None,
) -> str:
    """Open ``$EDITOR`` (or *editor*) and return the saved content.

    Parameters
    ----------
    prompt_text:  Informational message printed before opening the editor.
    initial_text: Pre-filled content placed in the temp file.
    extension:    Temp-file extension (helps editors pick syntax highlighting).
    editor:       Override the editor command; falls back to ``$EDITOR`` → ``nano``.
    """
    from ui.output import print_info
    print_info(prompt_text)

    editor_cmd = editor or os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=extension, delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(initial_text)
        tmp_path = tmp.name

    try:
        subprocess.run([editor_cmd, tmp_path], check=True)
        with open(tmp_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


# ── Form (multiple fields in one call) ───────────────────────────────

def ask_form(fields: List[dict[str, Any]]) -> dict[str, Any]:
    """Collect multiple values with a single call.

    Each element of *fields* is a ``dict`` with at minimum ``"name"`` and
    ``"prompt"`` keys.  Additional keys map to the kwargs of the underlying
    ``ask_*`` function selected by ``"type"``.

    Supported field types
    ---------------------
    ``"text"`` (default), ``"secret"``, ``"int"``, ``"float"``,
    ``"confirm"``, ``"select"``, ``"multiselect"``, ``"file"``,
    ``"directory"``, ``"autocomplete"``, ``"editor"``.

    Example::

        result = ask_form([
            {"name": "username", "prompt": "Username"},
            {"name": "password", "prompt": "Password", "type": "secret"},
            {"name": "age",      "prompt": "Age",      "type": "int", "min_value": 0},
            {"name": "role",     "prompt": "Role",     "type": "select",
             "options": ["admin", "user", "viewer"]},
        ])
        # result == {"username": "alice", "password": "…", "age": 30, "role": "user"}

    Parameters
    ----------
    fields: List of field definition dicts (see above).
    """
    _DISPATCH: dict[str, Callable[..., Any]] = {
        "text": ask_input,
        "secret": ask_secret,
        "int": ask_int,
        "float": ask_float,
        "confirm": ask_confirm,
        "select": ask_select,
        "multiselect": ask_multiselect,
        "file": ask_file,
        "directory": ask_directory,
        "autocomplete": ask_autocomplete,
        "editor": ask_editor,
    }

    result: dict[str, Any] = {}
    for field in fields:
        field = dict(field)  # shallow copy
        name = field.pop("name")
        prompt_text = field.pop("prompt")
        field_type = field.pop("type", "text")

        fn = _DISPATCH.get(field_type)
        if fn is None:
            raise ValueError(f"Unknown field type: {field_type!r}")

        result[name] = fn(prompt_text, **field)
    return result
