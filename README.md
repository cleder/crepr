# crepr

Create a ``__repr__`` for your python classes.


`crepr` is a Python script that takes a file name as a command-line argument, imports the specified module, and then adds or removes a `__repr__` method for each class defined in the module. It uses the definition found in the  `__init__` method of the class to create a useful representation of the object.
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


## Features

* Automatically generates `__repr__` methods for all classes in a Python file
* Uses the `__init__` method's arguments to create a meaningful representation
* Can add or remove `__repr__` methods
* Provides options to display the diff or apply changes directly to the file

## Install

```bash
pip install crepr
```

## Usage

To add a `__repr__` method to all classes in a file:

```bash
crepr add <file_name> [--kwarg-splat "..."] [--diff/--inline]
```

To remove the `__repr__` method from all classes in a file:

```bash
crepr remove <file_name> [--diff/--inline]
```

### Options

* `<file_name>`: The name of the Python file to process.
* `--kwarg-splat`: The string to use for the **kwargs splat (default: "...").
* `--diff`: Display the diff of the changes.
* `--inline`: Apply the changes directly to the file.

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
