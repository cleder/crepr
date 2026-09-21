---
title: "Source Inspection"
description: "Reference the functions crepr uses to load modules, inspect methods, and choose supported classes."
---

This page covers the public helper functions that turn source files into inspectable Python objects. All definitions live in `crepr/crepr.py`.

## Method Source Helpers

### `get_method_source`

Import path: `from crepr.crepr import get_method_source`

Signature:

```python
def get_method_source(cls: type, method_name: str) -> tuple[str, int]: ...
```

Returns the source text and starting line number for a method declared directly on `cls`. If the method is absent or `inspect` cannot recover the source, the function returns `("", -1)`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cls` | `type` | — | Class to inspect. |
| `method_name` | `str` | — | Name of the method to locate. |

Return type: `tuple[str, int]`

Example:

```python
source, line = get_method_source(module.Account, "__init__")
```

### `get_init_source`

Import path: `from crepr.crepr import get_init_source`

Signature:

```python
def get_init_source(cls: type) -> tuple[str, int]: ...
```

Thin wrapper around `get_method_source(cls, "__init__")`.

### `get_repr_source`

Import path: `from crepr.crepr import get_repr_source`

Signature:

```python
def get_repr_source(cls: type) -> tuple[str, int]: ...
```

Thin wrapper around `get_method_source(cls, "__repr__")`.

## Constructor And Class Filters

### `get_init_args`

Import path: `from crepr.crepr import get_init_args`

Signature:

```python
def get_init_args(
    cls: type,
) -> tuple[MappingProxyType[str, inspect.Parameter] | None, int, list[str]]: ...
```

Returns the constructor parameter mapping, the constructor starting line number, and the constructor source lines. If the class does not define `__init__` directly, the function returns `(None, -1, [])`.

Example:

```python
init_args, line, source_lines = get_init_args(module.Account)
```

### `has_only_kwargs`

Import path: `from crepr.crepr import has_only_kwargs`

Signature:

```python
def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool: ...
```

Returns `True` when every parameter is one of:

- `POSITIONAL_OR_KEYWORD`
- `KEYWORD_ONLY`
- `VAR_KEYWORD`

It returns `False` for constructors with `VAR_POSITIONAL` (`*args`).

### `is_class_in_module`

Import path: `from crepr.crepr import is_class_in_module`

Signature:

```python
def is_class_in_module(cls: type, module: ModuleType) -> bool: ...
```

Checks whether a class is defined in the loaded module rather than imported into it.

### `repr_exists`

Import path: `from crepr.crepr import repr_exists`

Signature:

```python
def repr_exists(cls: type) -> bool: ...
```

Returns `True` when `__repr__` exists in `cls.__dict__`.

### `get_all_init_args`

Import path: `from crepr.crepr import get_all_init_args`

Signature:

```python
def get_all_init_args(
    module: ModuleType,
) -> Iterator[
    tuple[type, MappingProxyType[str, inspect.Parameter], int, list[str]]
]: ...
```

Iterates through all classes in the module, applies the class-selection rules, and yields tuples ready for repr generation or removal.

Example:

```python
for cls, init_args, line, source in get_all_init_args(module):
    print(cls.__name__, line, list(init_args))
```

## Module Loading

### `get_module`

Import path: `from crepr.crepr import get_module`

Signature:

```python
def get_module(file_path: pathlib.Path) -> ModuleType: ...
```

Loads a file into a uniquely named module using `spec_from_file_location` and `module_from_spec`. Raises `CreprError` on spec creation failure, import failure, or syntax failure.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | `pathlib.Path` | — | Python source file to import and inspect. |

Return type: `ModuleType`

Example:

```python
from pathlib import Path

module = get_module(Path("models.py"))
```

### `get_modules`

Import path: `from crepr.crepr import get_modules`

Signature:

```python
def get_modules(
    files: Iterable[pathlib.Path],
) -> Iterator[tuple[ModuleType, pathlib.Path]]: ...
```

Attempts to load each file and yields only the successful `(module, path)` pairs. Errors are printed and skipped.

Example:

```python
from pathlib import Path

for module, path in get_modules([Path("a.py"), Path("b.py")]):
    print(path, module.__name__)
```

## Common Combination Pattern

The most common programmatic workflow is:

```python
from pathlib import Path
from crepr.crepr import get_all_init_args, get_module

module = get_module(Path("models.py"))

for cls, init_args, line, source in get_all_init_args(module):
    print(cls.__name__, list(init_args.keys()), line, len(source))
```

That gives you the same class-discovery view that `add` and `remove` use internally, without yet generating or mutating source.
