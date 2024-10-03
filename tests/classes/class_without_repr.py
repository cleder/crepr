"""Module containing class definitions for testing purposes.

This module defines a class without a `__repr__` method.
"""

from typing import Self


class MyClassWithoutRepr:
    """A class without a `__repr__` method."""

    def __init__(self: Self, value: str) -> None:
        """Initialize the class with the given value."""
        self.value = value
