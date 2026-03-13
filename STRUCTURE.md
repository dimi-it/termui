# Project Structure

This project follows the modern Python package layout with `src/` directory structure.

```
termui/
│
├── pyproject.toml        # Project configuration (modern standard)
├── README.md             # Project description
├── LICENSE               # MIT License
├── .gitignore            # Git ignored files
├── requirements.txt      # Legacy requirements (optional)
│
├── src/                  # Source code
│   └── termui/           # Main package
│       ├── __init__.py           # Public API exports
│       ├── console.py            # Shared rich Console singleton
│       ├── theme.py              # Theme configuration
│       ├── output.py             # Rich output helpers
│       ├── input.py              # Prompt-toolkit input helpers
│       ├── layout.py             # Multi-column layouts & dashboards
│       ├── termui_logging.py     # Rich logging handler
│       ├── notify.py             # Terminal notifications
│       └── diff.py               # Diff rendering
│
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_output.py    # Example test file
│
├── scripts/              # CLI and helper scripts
│   └── demo.py           # Comprehensive demo of all features
│
└── docs/                 # Documentation
    └── getting_started.md
```

## Installation

```bash
# Install in development mode (editable)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install from source
pip install .
```

## Usage

```python
from termui import print_header, print_success, spinner

print_header("My App", subtitle="v1.0")

with spinner("Processing..."):
    # do work
    pass

print_success("Done!")
```

## Running the Demo

```bash
python scripts/demo.py
```

## Running Tests

```bash
pytest
```

## Benefits of This Structure

1. **Modern Standard**: Follows PEP 517/518 with `pyproject.toml`
2. **Isolated Source**: `src/` layout prevents accidental imports
3. **Clean Namespace**: Package installed properly via pip
4. **Testable**: Tests can import the installed package
5. **Distributable**: Ready for PyPI publishing
6. **Professional**: Industry-standard Python project layout
