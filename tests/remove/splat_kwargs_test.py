"""Test a class with keyword arguments and **kwargs."""

from typing import Self


class SplatKwargs:
    """The happy path class."""

    def __init__(self: Self, name: str, **kwargs: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.kwargs = kwargs  # pragma: no cover

    def __repr__(self: Self) -> str:
        """Create a string (c)representation for SplatKwargs."""
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"**kwargs=...,"
            ")"
        )
