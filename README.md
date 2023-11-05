# crepr

Create a ``__repr__`` for your python classes.

A Python script that takes a file path as a command-line argument,
imports the specified file, and creates a `__repr__` method
for each class defined in the module.
It uses the definition found in the  `__init__` method of the class.
It is pronounced /kɹeɪpr/, like 🇳🇿 crêpe.

[![Tests](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml/badge.svg)](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml)
[![codecov](https://codecov.io/gh/cleder/crepr/graph/badge.svg?token=EGCcrWkpay)](https://codecov.io/gh/cleder/crepr)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)
](https://github.com/pre-commit/pre-commit)
[![MyPy](https://img.shields.io/badge/type_checker-mypy-blue)
](http://mypy-lang.org/)
[![Black](https://img.shields.io/badge/code_style-black-000000)
](https://github.com/psf/black)

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

Given the file `tests/classes/kw_only_test.py` with the contents:

```
class KwOnly:
    def __init__(self, name: str, *, age: int) -> None:
        self.name = name
        self.age = age
```

The command:

```
❯ crepr tests/kw_only_test.py
```

produces

```
class KwOnly:
    def __init__(self, name: str, *, age: int) -> None:
        self.name = name
        self.age = age

    def __repr__(self) -> str:
        """Create a string (c)representation for KwOnly."""
        return (f'{self.__class__.__module__}.{self.__class__.__name__}('
            f'name={self.name!r}, '
            f'age={self.age!r}, '
        ')')
```

The `repr()` of an instance of this class will be:

```
>>> from tests.classes.kw_only_test import KwOnly
>>> kwo = KwOnly('Christian', age=25)
>>> kwo
tests.classes.kw_only_test.KwOnly(name='Christian', age=25, )
```

Give your representations some love.

❤️`.__repr__(self) -> str:`
