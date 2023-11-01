# crepr

Create a ``__repr__`` for your python classes.

A Python script that takes a module name as a command-line argument,
imports the specified module, and then prints a `__repr__` method
for each class defined in the module.
It uses the definition found in the  `__init__` method of the class.

For a class with

```python
    def __init__(
        self,
        ns: Optional[str] = None,
        href: Optional[str] = None,
        rel: Optional[str] = None,
        type: Optional[str] = None,
        hreflang: Optional[str] = None,
        title: Optional[str] = None,
        length: Optional[int] = None,
    ) -> None:
```

it will create

```python
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"ns={self.ns!r}, "
            f"href={self.href!r}, "
            f"rel={self.rel!r}, "
            f"type={self.type!r}, "
            f"hreflang={self.hreflang!r}, "
            f"title={self.title!r}, "
            f"length={self.length!r}, "
            ")"
        )
```
