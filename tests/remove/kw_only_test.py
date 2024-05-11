"""Test class for kw only arguments."""

from typing import Self


class KwOnly:
    """The happy path class."""

    def __init__(self: Self, name: str, *, age: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.age = age  # pragma: no cover

    def __repr__(self: Self) -> str:
        """Create a string (c)representation for KwOnly."""
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"age={self.age!r}, "
            ")"
        )
