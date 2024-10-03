"""Module containing class definitions for testing purposes.

This module defines a class with a `__repr__` method.
"""

from typing import Self


class MyClassWithRepr:
    """A class without a `__repr__` method."""

    def __init__(self: Self, value: str) -> None:
        """Initialize the class with the given value."""
        self.value = value

    def __repr__(self: Self) -> str:
        """Create a string (c)representation for MyClassWithRepr."""
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}("
            f"value={self.value!r}, "
            ")"
        )
