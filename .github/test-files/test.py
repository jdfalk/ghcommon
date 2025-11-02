#!/usr/bin/env python3
# file: .github/test-files/test.py
# version: 1.0.0
# guid: b7c8d9e0-f1a2-3b4c-5d6e-7f8a9b0c1d2e

"""Test Python File.

Purpose: Test Python linting with Black, Pylint, Flake8, isort, and mypy.
"""


class TestClass:
    """Test class for Python linting."""

    def __init__(self, name: str, value: int) -> None:
        """Initialize TestClass.

        Args:
            name: The name identifier
            value: The numeric value
        """
        self.name = name
        self.value = value

    def get_name(self) -> str:
        """Return the name."""
        return self.name

    def get_value(self) -> int:
        """Return the value."""
        return self.value

    def increment(self, amount: int = 1) -> int:
        """Increment the value.

        Args:
            amount: Amount to increment by (default: 1)

        Returns:
            The new value after incrementing
        """
        self.value += amount
        return self.value


def process_list(items: list[str], filter_empty: bool = True) -> list[str]:
    """Process a list of items.

    Args:
        items: List of string items to process
        filter_empty: Whether to filter out empty strings

    Returns:
        Processed list of items
    """
    if filter_empty:
        return [item.strip() for item in items if item.strip()]
    return [item.strip() for item in items]


def find_item(items: list[str], target: str) -> int | None:
    """Find the index of a target item.

    Args:
        items: List of items to search
        target: Target item to find

    Returns:
        Index of the item if found, None otherwise
    """
    try:
        return items.index(target)
    except ValueError:
        return None


def main() -> None:
    """Main entry point."""
    # Create test instance
    test_obj = TestClass("test", 10)
    print(f"Name: {test_obj.get_name()}")
    print(f"Value: {test_obj.get_value()}")

    # Increment value
    new_value = test_obj.increment(5)
    print(f"New value: {new_value}")

    # Process list
    items = ["  item1  ", "", "  item2  ", "item3"]
    processed = process_list(items)
    print(f"Processed items: {processed}")

    # Find item
    index = find_item(processed, "item2")
    if index is not None:
        print(f"Found 'item2' at index: {index}")
    else:
        print("Item not found")


if __name__ == "__main__":
    main()
