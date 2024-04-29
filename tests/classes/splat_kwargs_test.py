"""Test a class with keyword arguments and **kwargs."""

from typing import Self


class SplatKwargs:
    """The happy path class."""

    def __init__(self: Self, name: str, **kwargs: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.kwargs = kwargs  # pragma: no cover
