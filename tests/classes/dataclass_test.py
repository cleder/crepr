"""Test that it works with dataclasses."""

import dataclasses


@dataclasses.dataclass
class DC:
    """A dataclass."""

    x: int
    y: int


@dataclasses.dataclass(frozen=True)
class RegistryItem:
    """A registry item."""

    attr_name: str
    node_name: str
