# Python Code Style Guide

This guide follows Google's Python Style Guide and incorporates PEP 8 standards.

## Indentation and Line Length

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 80 characters
- Continue long lines using parentheses and indent the continued line
- For conditions with many clauses, put each clause on its own line

## Imports

- Import order: standard library, third-party, application-specific
- One import per line
- Absolute imports preferred over relative imports
- No wildcard imports (`from module import *`)
- Group imports by blank lines

```python
# Correct import ordering
import os
import sys

import numpy as np
import tensorflow as tf

from myproject.utils import helper
from myproject.core import models
```

## Naming Conventions

- `module_name`, `package_name`
- `ClassName`
- `method_name`, `function_name`
- `CONSTANT_NAME`
- `_private_attribute`
- `self` for instance method first argument
- `cls` for class method first argument

## Whitespace

- No trailing whitespace
- Surround binary operators with single space
- No space around keyword argument assignments
- Two blank lines between top-level functions and classes
- One blank line between method definitions

## Strings

- Use single quotes for simple strings
- Use double quotes for strings that contain single quotes
- Use triple double quotes for docstrings
- Use format strings (f-strings) for string formatting

## Comments and Documentation

- Use docstrings for all public modules, functions, classes, and methods
- Follow Google style for docstrings

```python
def fetch_data(source_url, timeout=10):
    """Fetches data from the specified URL.

    Args:
        source_url (str): The URL to fetch data from.
        timeout (int, optional): The timeout in seconds. Defaults to 10.

    Returns:
        dict: The fetched data as a dictionary.

    Raises:
        ConnectionError: If the connection fails.
    """
    # Implementation here
```

## Exception Handling

- Be specific about exceptions caught
- Use `as` syntax
- Limit the `try` clause to the necessary operations

## Classes

- Always use `self` for the first argument to instance methods
- Always use `cls` for the first argument to class methods
- Use properties for simple getters/setters
- Use explicit `super()` calls

## Other Recommendations

- Use list/dict/set comprehensions when appropriate
- Avoid using `+` operator to concatenate strings (use `join` or f-strings)
- Use `is` only for comparing with `None`, `True`, `False`
- Use context managers (`with` statement) when dealing with resources
- Use `typing` module for type hints

## Tool Configuration

- Use pylint, black, and isort for code formatting and linting
- Configure tools to match Google Python Style Guide
