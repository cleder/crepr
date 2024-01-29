"""Test class for kw only arguments."""

from typing import Self


class KwOnly:
    """The happy path class."""

    def __init__(self: Self, name: str, *, age: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.age = age  # pragma: no cover
