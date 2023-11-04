# crepr

Create a ``__repr__`` for your python classes.

A Python script that takes a file path as a command-line argument,
imports the specified file, and then prints a `__repr__` method
for each class defined in the module.
It uses the definition found in the  `__init__` method of the class.
It is pronounced like crêpe, the French pancake.

[![Tests](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml/badge.svg)](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml)
[![codecov](https://codecov.io/gh/cleder/crepr/graph/badge.svg?token=EGCcrWkpay)](https://codecov.io/gh/cleder/crepr)

## Install

```
pip install crepr
```

## Usage

```
❯ crepr --help
Usage: crepr [OPTIONS] FILE_PATH

  Create a __repr__ method for each class of a python file.

Arguments:
  FILE_PATH  [required]

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize
```

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

## Example

Given the file `tests/kw_only_test.py` with the contents:

```
class KwOnly:
    """The happy path class."""

    def __init__(self, name: str, *, age: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.age = age  # pragma: no cover
```

It will produce:

```
❯ crepr tests/kw_only_test.py
class KwOnly:
    """The happy path class."""

    def __init__(self, name: str, *, age: int) -> None:
        """Initialize the class."""
        self.name = name  # pragma: no cover
        self.age = age  # pragma: no cover

    def __repr__(self) -> str:
        """Create a string (c)representation of the class."""
        return (f'{self.__class__.__name__}('
            f'name={self.name!r}, '
            f'age={self.age!r}, '
        ')')

```
