"""Test class with positional args."""

from typing import Self


class PosArgs:
    """Positional args cannot be processed."""

    def __init__(self: Self, x: int, *args: int) -> None:
        """Initialize the class.

        Args:
        ----
            x (int): The value of x.
            *args (int): Additional arguments.

        Returns:
        -------
            None

        Examples:
        --------
            >>> obj = ClassName(10, arg1=20, arg2=30)

        """
