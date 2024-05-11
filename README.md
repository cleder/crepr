# crepr

Create a ``__repr__`` for your python classes.

A Python script that takes a file path as a command-line argument,
imports the specified file, and creates a `__repr__` method
for each class defined in the module.
It uses the definition found in the  `__init__` method of the class.
It is pronounced /kɹeɪpr/, like 🇳🇿 crêpe.

Have a look at the blog-post [Love Your Representation
](https://dev.to/ldrscke/love-your-representation-27mm) for the rationale of this package.

[![Tests](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml/badge.svg?branch=main)](https://github.com/cleder/crepr/actions/workflows/run-all-tests.yml)
[![codecov](https://codecov.io/gh/cleder/crepr/graph/badge.svg?token=EGCcrWkpay)](https://codecov.io/gh/cleder/crepr)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
](https://github.com/pre-commit/pre-commit)
[![MyPy](https://img.shields.io/badge/type_checker-mypy-blue)
](http://mypy-lang.org/)
[![Black](https://img.shields.io/badge/code_style-black-000000)
](https://github.com/psf/black)
[![MIT License](https://img.shields.io/pypi/l/crepr)](https://opensource.org/license/mit/)
[![Python Version](https://img.shields.io/pypi/pyversions/crepr)](https://www.python.org/)
[![PyPI - Version](https://img.shields.io/pypi/v/crepr)](https://pypi.org/project/crepr/)
[![Status](https://img.shields.io/pypi/status/crepr)](https://pypi.org/project/crepr/)

## Install

```bash
pip install crepr
```

## Usage

```bash
❯ crepr  --help
Usage: crepr [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  add     Add __repr__ to all classes in the source code.
  remove  Remove the __repr__ method from all classes in the source code.
```

### Add

The command `crepr add ...`  adds a `__repr__` method to all classes in this file, that
have a `__init__` method with no positional only arguments.

```bash
❯ crepr add  --help
Usage: crepr add [OPTIONS] FILES...

  Add __repr__ to all classes in the source code.

Arguments:
  FILES...  The python source file(s)  [required]

Options:
  --kwarg-splat TEXT  The **kwarg splat  [default: ...]
  --diff / --inline   Display the diff / Apply changes to the file(s)
  --help              Show this message and exit.
```

### Remove

The command `crepr remove ...` removes the `__repr__` methods from all classes that have
an `__init__` method with no positional only arguments.


```bash
❯ crepr remove  --help
Usage: crepr remove [OPTIONS] FILES...

  Remove the __repr__ method from all classes in the source code.

Arguments:
  FILES...  The python source file(s)  [required]

Options:
  --diff / --inline  Display the diff / Apply changes to the file(s)
  --help             Show this message and exit.
```

## Example

Given the file `tests/classes/kw_only_test.py` with the contents:

```python
class KwOnly:
    def __init__(self, name: str, *, age: int) -> None:
        self.name = name
        self.age = age
```

The command:

```bash
❯ crepr add tests/classes/kw_only_test.py
```

produces

```python
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

```python
>>> from tests.classes.kw_only_test import KwOnly
>>> kwo = KwOnly('Christian', age=25)
>>> kwo
tests.classes.kw_only_test.KwOnly(name='Christian', age=25, )
```

Apply the changes to the file with:

```bash
❯ crepr add tests/classes/kw_only_test.py --inline
```

Give your representations some love.

❤️`.__repr__(self) -> str:`
