# Getting Started with TermUI

## Installation

Install termui using pip:

```bash
pip install -e .
```

For development with testing tools:

```bash
pip install -e ".[dev]"
```

## Quick Example

```python
from termui import print_header, print_success, spinner
import time

print_header("My Application", subtitle="v1.0")

with spinner("Processing..."):
    time.sleep(2)

print_success("Done!")
```

## Running the Demo

To see all features in action:

```bash
python scripts/demo.py
```

## Next Steps

- Check out the [README](../README.md) for full API reference
- Browse example scripts in `scripts/`
- Read the source code in `src/termui/`
