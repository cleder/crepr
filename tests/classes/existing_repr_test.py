class ExistingRepr:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"ExistingRepr(name={self.name!r})"