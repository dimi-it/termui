"""ui.input — User-input helpers built on ``prompt_toolkit``.

All prompts use the active theme and share a single ``PromptSession``.
"""

from __future__ import annotations

import os
import re
import string
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import (
    Completer,
    FuzzyCompleter,
    PathCompleter,
    WordCompleter,
)
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.validation import ValidationError, Validator

from . import theme as _theme
from .output import print_error, print_table

T = TypeVar("T")

# ── Document-like dataclass (replaces duck-typed hack) ───────────────

@dataclass(frozen=True)
class _Document:
    """Minimal stand-in for ``prompt_toolkit.document.Document``.

    Used to feed raw strings into :class:`Validator` instances without
    resorting to dynamic ``type()`` hacks.
    """

    text: str


# ── Shared PromptSession ─────────────────────────────────────────────

_session: PromptSession[str] | None = None
_history: InMemoryHistory = InMemoryHistory()


def _get_session() -> PromptSession[str]:
    global _session
    if _session is None:
        _session = PromptSession(style=_theme.pt_style(), history=_history)
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
    def __init__(self, lo: float | None, hi: float | None, cast: type[int] | type[float]) -> None:
        self._lo = lo
        self._hi = hi
        self._cast = cast

    def validate(self, document: Any) -> None:
        text: str = document.text.strip()
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
    validator: Callable[[str], bool] | None = None,
    error_message: str = "Invalid input.",
    allow_empty: bool = False,
    history: bool = True,
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
    history:       Use ``prompt_toolkit`` in-memory history (↑ recalls).

    Examples
    --------
    >>> name = ask_input("Your name")
    """
    kwargs: dict[str, Any] = {"default": default}
    if not history:
        kwargs["history"] = InMemoryHistory()
    while True:
        result = _prompt(prompt_text, **kwargs)
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
    show_strength: bool = False,
) -> str:
    """Password / secret prompt that masks input.

    Parameters
    ----------
    prompt_text:    Label for the first prompt.
    confirm:        If ``True``, ask the user to re-enter for verification.
    confirm_prompt: Label for the confirmation prompt.
    show_strength:  Display a live password strength indicator.

    Examples
    --------
    >>> pw = ask_secret("Password", confirm=True, show_strength=True)
    """
    while True:
        value = _get_session().prompt(
            FormattedText([("class:prompt", f"{prompt_text} ❯ ")]),
            is_password=True,
        ).strip()
        if show_strength:
            strength = _password_strength(value)
            from .output import print_info
            print_info(f"Strength: {strength}")
        if not confirm:
            return value
        confirm_value = _get_session().prompt(
            FormattedText([("class:prompt", f"{confirm_prompt} ❯ ")]),
            is_password=True,
        ).strip()
        if value == confirm_value:
            return value
        print_error("Values do not match. Try again.")


def _password_strength(password: str) -> str:
    """Return a human-readable strength label for *password*.

    Returns
    -------
    str
        One of ``"very weak"``, ``"weak"``, ``"fair"``, ``"strong"``,
        ``"very strong"``.
    """
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c in string.ascii_lowercase for c in password):
        score += 1
    if any(c in string.ascii_uppercase for c in password):
        score += 1
    if any(c in string.digits for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1
    levels = ["very weak", "weak", "weak", "fair", "strong", "very strong", "very strong"]
    return levels[min(score, len(levels) - 1)]


# ── Numeric input ────────────────────────────────────────────────────

def ask_int(
    prompt_text: str,
    *,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Integer prompt with optional range validation.

    Parameters
    ----------
    prompt_text: Label shown before the cursor.
    default:     Pre-filled integer default.
    min_value:   Inclusive lower bound.
    max_value:   Inclusive upper bound.
    """
    v = _RangeValidator(min_value, max_value, int)
    label = prompt_text
    if min_value is not None or max_value is not None:
        bounds = f"{min_value or '−∞'} – {max_value or '+∞'}"
        label = f"{prompt_text} [{bounds}]"
    while True:
        raw = _prompt(label, default=str(default) if default is not None else "")
        try:
            v.validate(_Document(text=raw))
            return int(raw)
        except ValidationError as exc:
            print_error(str(exc.message))


def ask_float(
    prompt_text: str,
    *,
    default: float | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """Float prompt with optional range validation."""
    v = _RangeValidator(min_value, max_value, float)
    label = prompt_text
    while True:
        raw = _prompt(label, default=str(default) if default is not None else "")
        try:
            v.validate(_Document(text=raw))
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
    extensions: list[str] | None = None,
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
    options: list[str],
    *,
    default: int | None = None,
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
    options: list[str],
    *,
    min_choices: int = 1,
    max_choices: int | None = None,
) -> list[str]:
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


# ── Interactive arrow-key selection ──────────────────────────────────

def ask_select_interactive(
    prompt_text: str,
    options: list[str],
    *,
    default: int = 0,
    search: bool = True,
) -> str:
    """Interactive arrow-key single-choice menu.

    Uses ``prompt_toolkit``'s ``radiolist_dialog`` when available, falling
    back to :func:`ask_select` if the dialog cannot be created.

    Parameters
    ----------
    prompt_text : str
        Question displayed above the list.
    options : list[str]
        Choices.
    default : int
        0-based index of the default selection.
    search : bool
        Enable type-to-filter (header hint).

    Returns
    -------
    str
        The selected option string.

    Examples
    --------
    >>> choice = ask_select_interactive("Pick a model", ["gpt-4", "claude"])
    """
    try:
        from prompt_toolkit.shortcuts import radiolist_dialog
        result = radiolist_dialog(
            title=prompt_text,
            values=[(opt, opt) for opt in options],
            default=options[default] if default < len(options) else options[0],
        ).run()
        if result is None:
            return options[default]
        return str(result)
    except Exception:
        return ask_select(prompt_text, options, default=default + 1)


def ask_multiselect_interactive(
    prompt_text: str,
    options: list[str],
    *,
    min_choices: int = 1,
    max_choices: int | None = None,
    preselected: list[int] | None = None,
) -> list[str]:
    """Interactive arrow-key multi-choice menu with checkboxes.

    Uses ``prompt_toolkit``'s ``checkboxlist_dialog`` when available.

    Parameters
    ----------
    prompt_text : str
        Question displayed above the list.
    options : list[str]
        Choices.
    min_choices : int
        Minimum required selections.
    max_choices : int | None
        Maximum allowed selections.
    preselected : list[int] | None
        0-based indices of pre-checked options.

    Returns
    -------
    list[str]
        The selected option strings.

    Examples
    --------
    >>> picks = ask_multiselect_interactive("Features", ["streaming", "tools"])
    """
    try:
        from prompt_toolkit.shortcuts import checkboxlist_dialog
        defaults = [options[i] for i in (preselected or [])]
        while True:
            result = checkboxlist_dialog(
                title=prompt_text,
                values=[(opt, opt) for opt in options],
                default_values=defaults,
            ).run()
            selected: list[str] = [str(r) for r in (result or [])]
            if len(selected) < min_choices:
                print_error(f"Select at least {min_choices} option(s).")
                continue
            if max_choices and len(selected) > max_choices:
                print_error(f"Select at most {max_choices} option(s).")
                continue
            return selected
    except Exception:
        return ask_multiselect(
            prompt_text, options,
            min_choices=min_choices, max_choices=max_choices,
        )


# ── Date / datetime ──────────────────────────────────────────────────

def ask_date(
    prompt_text: str,
    *,
    default: date | None = None,
    fmt: str = "%Y-%m-%d",
) -> date:
    """Prompt the user for a date.

    Parameters
    ----------
    prompt_text : str
        Label shown before the cursor.
    default : date | None
        Pre-filled default.
    fmt : str
        Expected date format string.

    Returns
    -------
    date

    Examples
    --------
    >>> d = ask_date("Start date")
    """
    default_str = default.strftime(fmt) if default else ""
    while True:
        raw = _prompt(f"{prompt_text} ({fmt})", default=default_str)
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            print_error(f"Invalid date.  Expected format: {fmt}")


def ask_datetime(
    prompt_text: str,
    *,
    default: datetime | None = None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> datetime:
    """Prompt the user for a datetime.

    Parameters
    ----------
    prompt_text : str
        Label shown before the cursor.
    default : datetime | None
        Pre-filled default.
    fmt : str
        Expected datetime format string.

    Returns
    -------
    datetime

    Examples
    --------
    >>> dt = ask_datetime("Deadline")
    """
    default_str = default.strftime(fmt) if default else ""
    while True:
        raw = _prompt(f"{prompt_text} ({fmt})", default=default_str)
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            print_error(f"Invalid datetime.  Expected format: {fmt}")


# ── URL / email ──────────────────────────────────────────────────────

_URL_RE = re.compile(
    r"https?://"
    r"(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%])+"
)

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)


def ask_url(
    prompt_text: str,
    *,
    default: str = "",
) -> str:
    """Prompt for a URL with built-in validation.

    Parameters
    ----------
    prompt_text : str
        Label shown before the cursor.
    default : str
        Pre-filled default.

    Returns
    -------
    str
        Validated URL string.

    Examples
    --------
    >>> url = ask_url("API endpoint")
    """
    while True:
        raw = _prompt(prompt_text, default=default)
        if _URL_RE.fullmatch(raw):
            return raw
        print_error("Enter a valid URL (must start with http:// or https://).")


def ask_email(
    prompt_text: str,
    *,
    default: str = "",
) -> str:
    """Prompt for an email address with built-in validation.

    Parameters
    ----------
    prompt_text : str
        Label shown before the cursor.
    default : str
        Pre-filled default.

    Returns
    -------
    str
        Validated email string.

    Examples
    --------
    >>> email = ask_email("Contact email")
    """
    while True:
        raw = _prompt(prompt_text, default=default)
        if _EMAIL_RE.fullmatch(raw):
            return raw
        print_error("Enter a valid email address (e.g. user@example.com).")


# ── Autocomplete ─────────────────────────────────────────────────────

def ask_autocomplete(
    prompt_text: str,
    completions: list[str],
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
    editor: str | None = None,
) -> str:
    """Open ``$EDITOR`` (or *editor*) and return the saved content.

    Parameters
    ----------
    prompt_text:  Informational message printed before opening the editor.
    initial_text: Pre-filled content placed in the temp file.
    extension:    Temp-file extension (helps editors pick syntax highlighting).
    editor:       Override the editor command; falls back to ``$EDITOR`` → ``nano``.
    """
    from .output import print_info
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

def ask_form(fields: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect multiple values with a single call.

    Each element of *fields* is a ``dict`` with at minimum ``"name"`` and
    ``"prompt"`` keys.  Additional keys map to the kwargs of the underlying
    ``ask_*`` function selected by ``"type"``.

    Supported field types
    ---------------------
    ``"text"`` (default), ``"secret"``, ``"int"``, ``"float"``,
    ``"confirm"``, ``"select"``, ``"multiselect"``, ``"file"``,
    ``"directory"``, ``"autocomplete"``, ``"editor"``.

    Validation hooks
    ----------------
    Each field dict may include a ``"validate"`` key — a
    ``Callable[[Any], str | None]`` that returns an error message or ``None``.
    The field is re-prompted until validation passes.

    Conditional fields
    ------------------
    A ``"depends_on"`` key with ``{"field": "name", "value": expected}``
    causes the field to be skipped unless a previously collected value
    matches.

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
    for field_def in fields:
        field_def = dict(field_def)  # shallow copy
        name: str = field_def.pop("name")
        prompt_text: str = field_def.pop("prompt")
        field_type: str = field_def.pop("type", "text")
        validate_fn: Callable[[Any], str | None] | None = field_def.pop("validate", None)
        depends_on: dict[str, Any] | None = field_def.pop("depends_on", None)

        # Conditional field — skip if dependency not met
        if depends_on is not None:
            dep_field = depends_on.get("field", "")
            dep_value = depends_on.get("value")
            if result.get(dep_field) != dep_value:
                continue

        fn = _DISPATCH.get(field_type)
        if fn is None:
            raise ValueError(f"Unknown field type: {field_type!r}")

        while True:
            value = fn(prompt_text, **field_def)
            if validate_fn is not None:
                error = validate_fn(value)
                if error is not None:
                    print_error(error)
                    continue
            break
        result[name] = value
    return result
