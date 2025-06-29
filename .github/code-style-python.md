<!-- file: copilot/code-style-python.md -->
<!-- version: 1.0.0 -->
<!-- guid: 2a5b7c8d-9e1f-4a2b-8c3d-6e9f1a5b7c8d -->

# Python Code Style Guide (Google Style)

This file provides Python coding style guidelines based on Google's Python Style Guide.

## Overview

Python is the main dynamic language used at Google. This style guide is a list of dos and don'ts for Python programs that follows Google's comprehensive style guide.

## Key Principles

- **BE CONSISTENT**: Follow the established patterns in your codebase
- **Readability counts**: Code is read more often than it is written
- **Simple is better than complex**: Prefer clarity over cleverness
- **Use tools**: Leverage formatters like `ruff`, `black`, and `isort` for consistency

## Language Rules

### 2.1 Linting

- **Run `pylint` on your code** using Google's pylintrc configuration
- Suppress warnings with `# pylint: disable=warning-name` when appropriate
- Always include explanatory comments for suppressions

### 2.2 Imports

- Use `import x` for importing packages and modules
- Use `from x import y` where `x` is the package prefix and `y` is the module name
- Use `from x import y as z` for disambiguation or overly long names
- **Import each module using the full pathname location**
- Do not use relative imports

```python
# Yes
from absl import flags
from doctor.who import jodie

# No
import jodie  # Unclear which module
```

### 2.3 Packages

- Import each module by its full package name
- Avoid assuming current directory is in `sys.path`

### 2.4 Exceptions

- Use built-in exception classes when appropriate
- Do not use `assert` for critical application logic
- Never use catch-all `except:` statements
- Minimize code in `try`/`except` blocks
- Use `finally` for cleanup

### 2.5 Mutable Global State

- **Avoid mutable global state**
- Use module-level constants with ALL_CAPS naming
- Make mutable globals internal with `_` prefix

### 2.6 Nested Functions and Classes

- Use nested functions when closing over a local value
- Don't nest just to hide from module users - use `_` prefix instead

### 2.7 Comprehensions

- Use comprehensions for simple cases
- Avoid multiple `for` clauses or complex filter expressions
- Optimize for readability, not conciseness

```python
# Yes
result = [mapping_expr for value in iterable if filter_expr]

# No
result = [(x, y) for x in range(10) for y in range(5) if x * y > 10]
```

### 2.8 Default Iterators and Operators

- Use default iterators: `for key in dict:` not `for key in dict.keys():`
- Use built-in operators when available

### 2.9 Generators

- Use generators as needed
- Use "Yields:" rather than "Returns:" in docstrings
- Manage expensive resources with context managers

### 2.10 Lambda Functions

- Okay for one-liners
- Prefer generator expressions over `map()` or `filter()` with lambda
- Use `operator` module functions when possible

### 2.11 Conditional Expressions

- Use for simple cases only
- Each portion must fit on one line

```python
# Yes
one_line = 'yes' if predicate(value) else 'no'

# No
bad_line_breaking = ('yes' if predicate(value) else
                     'no')
```

### 2.12 Default Argument Values

- Do not use mutable objects as default values
- Use `None` and check in function body

```python
# Yes
def foo(a, b=None):
    if b is None:
        b = []

# No
def foo(a, b=[]):
    ...
```

### 2.13 Properties

- Use properties for simple computations only
- Properties should be cheap, straightforward, and unsurprising
- Use `@property` decorator

### 2.14 True/False Evaluations

- Use implicit false when possible: `if foo:` not `if foo != []:`
- Always use `if foo is None:` for None checks
- Never compare booleans with `==`

## Style Rules

### 3.1 Semicolons

- **Do not terminate lines with semicolons**
- Do not put two statements on the same line

### 3.2 Line Length

- **Maximum line length is 80 characters**
- Use parentheses for implicit line continuation
- Do not use backslashes for line continuation

Exceptions:

- Long import statements
- URLs, pathnames, or long flags in comments
- Long string constants
- Pylint disable comments

### 3.3 Parentheses

- Use parentheses sparingly
- Don't use them in return statements or conditionals unless needed
- Use them for tuples and implied line continuation

### 3.4 Indentation

- **Indent code blocks with 4 spaces**
- Never use tabs
- Align wrapped elements vertically or use hanging 4-space indent

```python
# Yes - Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                        var_three, var_four)

# Yes - 4-space hanging indent
foo = long_function_name(
    var_one, var_two, var_three,
    var_four)
```

### 3.5 Blank Lines

- **Two blank lines between top-level definitions**
- **One blank line between method definitions**
- **No blank line following a `def` line**

### 3.6 Whitespace

- No whitespace inside parentheses, brackets, or braces
- No whitespace before commas, semicolons, or colons
- Surround binary operators with single space
- No spaces around `=` in keyword arguments (except with type annotations)

```python
# Yes
spam(ham[1], {'eggs': 2}, [])
if x == 4:
    print(x, y)

# No
spam( ham[ 1 ], { 'eggs': 2 }, [ ] )
if x == 4 :
    print(x , y)
```

### 3.7 Shebang Line

- Use `#!/usr/bin/env python3` for executable files
- Only needed for files intended to be executed directly

### 3.8 Comments and Docstrings

#### Docstrings

- **Always use triple-double-quotes `"""`**
- Start with one-line summary (≤80 chars) ending with period
- Use Google-style docstring format

```python
def fetch_data(table_handle: Table, keys: Sequence[str]) -> Dict[str, Any]:
    """Fetches data from the specified table.

    Args:
        table_handle: An open table instance.
        keys: A sequence of strings representing the keys to fetch.

    Returns:
        A dict mapping keys to the corresponding data.

    Raises:
        IOError: An error occurred accessing the table.
    """
```

#### Modules

- Start with license boilerplate
- Include module docstring describing contents and usage

#### Functions and Methods

- Document public APIs, nontrivial size, and non-obvious logic
- Use sections: Args, Returns/Yields, Raises

#### Classes

- Include class docstring describing the class
- Document public attributes in Attributes section

#### Comments

- Use for tricky parts of code
- Start 2 spaces from code with `# `
- Don't describe obvious code

### 3.10 Strings

- Use f-strings, `%` operator, or `format()` for formatting
- Don't use `+` for string formatting
- Use `''.join()` for accumulating strings in loops
- Be consistent with quote choice (`'` or `"`)
- Prefer `"""` for multi-line strings

### 3.11 Files and Sockets

- **Explicitly close files and sockets**
- Use `with` statements for resource management
- Use `contextlib.closing()` for objects without context manager support

### 3.12 TODO Comments

- Format: `# TODO: crbug.com/192795 - Description`
- Include context link and explanation
- Avoid referencing individuals

### 3.13 Import Formatting

- Imports on separate lines (except typing and collections.abc)
- Group from most to least generic:
  1. `__future__` imports
  2. Standard library
  3. Third-party modules
  4. Local sub-packages
- Sort lexicographically within groups

### 3.14 Statements

- Generally one statement per line
- May put simple test result on same line as test

### 3.15 Getters and Setters

- Use when providing meaningful behavior
- Follow naming: `get_foo()` and `set_foo()`
- Consider properties for simple logic

### 3.16 Naming

#### Names to Avoid

- Single character names (except counters, exceptions, file handles)
- Dashes in package/module names
- `__double_leading_and_trailing_underscore__` names

#### Conventions

- `module_name`, `package_name`
- `ClassName`, `ExceptionName`
- `function_name`, `method_name`
- `GLOBAL_CONSTANT_NAME`
- `global_var_name`, `instance_var_name`
- `function_parameter_name`, `local_var_name`

#### Guidelines

| Type                       | Public               | Internal              |
| -------------------------- | -------------------- | --------------------- |
| Packages                   | `lower_with_under`   |                       |
| Modules                    | `lower_with_under`   | `_lower_with_under`   |
| Classes                    | `CapWords`           | `_CapWords`           |
| Exceptions                 | `CapWords`           |                       |
| Functions                  | `lower_with_under()` | `_lower_with_under()` |
| Global/Class Constants     | `CAPS_WITH_UNDER`    | `_CAPS_WITH_UNDER`    |
| Global/Class Variables     | `lower_with_under`   | `_lower_with_under`   |
| Instance Variables         | `lower_with_under`   | `_lower_with_under`   |
| Method Names               | `lower_with_under()` | `_lower_with_under()` |
| Function/Method Parameters | `lower_with_under`   |                       |
| Local Variables            | `lower_with_under`   |                       |

### 3.17 Main

- Put main functionality in `main()` function
- Always check `if __name__ == '__main__':`
- Use `app.run(main)` with absl, otherwise call `main()` directly

### 3.18 Function Length

- **Prefer small and focused functions**
- Consider breaking up functions over ~40 lines
- Long functions are sometimes appropriate

### 3.19 Type Annotations

- **Strongly encouraged for new code**
- Use for public APIs and complex code
- Follow PEP 484 conventions
- Use `from __future__ import annotations` for forward declarations

```python
def func(a: int, b: str = "default") -> bool:
    """Example function with type annotations."""
    return len(b) > a
```

## Tools and Configuration

### Recommended Tools

- **ruff**: Primary linter and formatter (replaces black, isort, flake8)
- **pylint**: Additional static analysis with Google's pylintrc
- **mypy** or **pytype**: Type checking

### Configuration Files

- `.ruff.toml`: Configure ruff for Google style compliance
- `.pylintrc`: Google's pylint configuration
- `pyproject.toml`: Project metadata and tool configuration

## Examples

### Good Python Code

```python
"""Module for processing user data."""

from typing import Dict, List, Optional
import logging


class UserProcessor:
    """Processes user data according to business rules."""

    def __init__(self, config: Dict[str, str]) -> None:
        """Initialize processor with configuration.

        Args:
            config: Configuration dictionary with processing parameters.
        """
        self._config = config
        self._cache: Dict[str, User] = {}

    def process_users(self, users: List[User]) -> List[ProcessedUser]:
        """Process a list of users.

        Args:
            users: List of user objects to process.

        Returns:
            List of processed user objects.

        Raises:
            ProcessingError: If processing fails for any user.
        """
        results = []
        for user in users:
            try:
                processed = self._process_single_user(user)
                results.append(processed)
            except Exception as e:
                logging.error('Failed to process user %s: %s', user.id, e)
                raise ProcessingError(f'Processing failed for user {user.id}') from e

        return results

    def _process_single_user(self, user: User) -> ProcessedUser:
        """Process a single user."""
        if user.id in self._cache:
            return self._cache[user.id]

        # Complex processing logic here
        processed = ProcessedUser(
            id=user.id,
            name=user.name.title(),
            email=user.email.lower(),
            status='active' if user.is_verified else 'pending'
        )

        self._cache[user.id] = processed
        return processed


def main() -> None:
    """Main entry point."""
    config = load_config()
    processor = UserProcessor(config)
    users = load_users()

    try:
        processed_users = processor.process_users(users)
        save_processed_users(processed_users)
        logging.info('Successfully processed %d users', len(processed_users))
    except ProcessingError as e:
        logging.error('Processing failed: %s', e)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
```

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google Python pylintrc](https://google.github.io/styleguide/pylintrc)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
