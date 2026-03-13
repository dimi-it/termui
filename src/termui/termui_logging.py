"""ui.logging — Drop-in ``logging.Handler`` that renders through rich.

Usage
-----
    from ui.logging import get_logger

    log = get_logger("my_agent")
    log.info("Model loaded")
    log.warning("Context window at 80 %%")
    log.error("API call failed", exc_info=True)

Structured fields can be passed via the ``extra`` dict::

    log.info("Request finished", extra={"fields": {"status": 200, "latency_ms": 42}})

Or, to integrate with an existing ``logging`` hierarchy::

    import logging
    from ui.logging import RichHandler

    logging.basicConfig(handlers=[RichHandler()], level=logging.DEBUG)
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from rich.text import Text

from .console import console, console_lock
from . import theme as _theme


# ── Handler ──────────────────────────────────────────────────────────

class RichHandler(logging.Handler):
    """A ``logging.Handler`` that renders log records via the shared ``rich``
    console with timestamps, coloured level labels, and optional tracebacks.

    Structured fields
    -----------------
    If the log record has ``extra["fields"]`` (a dict), the key=value pairs
    are rendered inline as dim text after the message.

    Parameters
    ----------
    show_time:   Include a timestamp column.
    show_path:   Include the module/filename:lineno column.
    markup:      Allow rich markup in log messages.
    level:       Minimum log level to handle.
    """

    LEVEL_STYLES: dict[int, str] = {
        logging.DEBUG:    "dim cyan",
        logging.INFO:     "bold cyan",
        logging.WARNING:  "bold yellow",
        logging.ERROR:    "bold red",
        logging.CRITICAL: "bold white on red",
    }

    LEVEL_ICONS: dict[int, str] = {
        logging.DEBUG:    "·",
        logging.INFO:     "ℹ",
        logging.WARNING:  "⚠",
        logging.ERROR:    "✘",
        logging.CRITICAL: "☠",
    }

    def __init__(
        self,
        *,
        show_time: bool = True,
        show_path: bool = False,
        markup: bool = True,
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level)
        self.show_time = show_time
        self.show_path = show_path
        self.markup = markup

    def emit(self, record: logging.LogRecord) -> None:
        t = _theme.current()
        level_style = self.LEVEL_STYLES.get(record.levelno, "")
        icon = self.LEVEL_ICONS.get(record.levelno, "•")
        level_name = record.levelname.ljust(8)

        parts: list[str] = []

        if self.show_time:
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            parts.append(f"[dim]{ts}[/dim]")

        parts.append(f"[{level_style}]{icon} {level_name}[/{level_style}]")

        if self.show_path:
            path = f"{record.module}:{record.lineno}"
            parts.append(f"[dim]{path}[/dim]")

        msg = record.getMessage()
        parts.append(msg)

        # Structured fields support
        fields: dict[str, Any] | None = getattr(record, "fields", None)
        if fields and isinstance(fields, dict):
            field_parts = " ".join(f"[dim]{k}={v}[/dim]" for k, v in fields.items())
            parts.append(field_parts)

        with console_lock:
            console.print(" ".join(parts), markup=self.markup, highlight=False)

            if record.exc_info:
                console.print_exception(extra_lines=1)


# ── Convenience factory ──────────────────────────────────────────────

def get_logger(
    name: str,
    *,
    level: int = logging.DEBUG,
    show_time: bool = True,
    show_path: bool = False,
    log_file: Path | str | None = None,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """Return a ``Logger`` pre-configured with a ``RichHandler``.

    Repeated calls with the same *name* return the same logger (standard
    Python logging behaviour) but will not add duplicate handlers.

    Parameters
    ----------
    name:       Logger name (typically the module or agent name).
    level:      Minimum level to capture.
    show_time:  Show timestamps in output.
    show_path:  Show ``module:lineno`` source location.
    log_file:   Optional file path for a plain-text ``FileHandler`` (no ANSI).
    file_level: Minimum level for the file handler.

    Examples
    --------
    >>> log = get_logger("agent", log_file="/tmp/agent.log")
    >>> log.info("Ready")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(show_time=show_time, show_path=show_path, level=level)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # avoid double-printing to root logger

    # File handler — plain text, no ANSI escape codes
    if log_file is not None:
        # Avoid adding duplicate file handlers
        has_file_handler = any(
            isinstance(h, logging.FileHandler) for h in logger.handlers
        )
        if not has_file_handler:
            fh = logging.FileHandler(str(log_file), encoding="utf-8")
            fh.setLevel(file_level)
            fh.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
            )
            logger.addHandler(fh)

    return logger


# ── Level helper ─────────────────────────────────────────────────────

def set_level(name: str, level: int) -> None:
    """Set the log level for a named logger.

    Parameters
    ----------
    name : str
        Logger name.
    level : int
        Standard logging level (e.g. ``logging.INFO``).

    Examples
    --------
    >>> set_level("agent", logging.WARNING)
    """
    logging.getLogger(name).setLevel(level)


# ── capture_logs context manager ─────────────────────────────────────

@contextmanager
def capture_logs(logger_name: str) -> Generator[list[logging.LogRecord], None, None]:
    """Temporarily capture log records for testing.

    Attaches a ``logging.handlers.MemoryHandler`` (capacity=10000) and
    yields the accumulated list of :class:`logging.LogRecord` objects.
    The handler is removed on exit.

    Parameters
    ----------
    logger_name : str
        Name of the logger to capture from.

    Yields
    ------
    list[logging.LogRecord]
        Mutable list that grows as records are emitted.

    Examples
    --------
    >>> with capture_logs("myapp") as records:
    ...     log = get_logger("myapp")
    ...     log.info("hello")
    >>> assert len(records) == 1
    >>> assert "hello" in records[0].getMessage()
    """
    logger = logging.getLogger(logger_name)
    records: list[logging.LogRecord] = []

    class _ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _ListHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
