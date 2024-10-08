"""Test class for kw only arguments."""

import dataclasses
from typing import Self


class ExistingRepr:
    """The class to test behaviour with existing repr."""

    def __init__(self: Self, name: str) -> None:
        """Initialize the class."""
        self.name = name

    def __repr__(self: Self) -> str:
        """Existing repr magic method of the class."""
        return f"ExistingRepr(name={self.name!r})"


class NoRepr:
    """The class to test behaviour with existing repr."""

    def __init__(self: Self, name: str) -> None:
        """Initialize the class."""
        self.name = name


@dataclasses.dataclass
class TestDataClass:
    """A simple dataclass for testing ignore existing flag."""

    number: int


@dataclasses.dataclass(frozen=True)
class TestDataClassFrozen:
    """A simple frozen dataclass for testing ignore existing flag."""

    number: int
