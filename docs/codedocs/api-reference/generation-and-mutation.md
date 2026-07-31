---
title: "Generation And Mutation"
description: "Reference the functions that build repr lines, construct change maps, and apply edits to source files."
---

This page documents the public functions that transform selected classes into source edits. All definitions are in `crepr/crepr.py`.

## Generation Functions

### `create_repr_lines`

Import path: `from crepr.crepr import create_repr_lines`

Signature:

```python
def create_repr_lines(
    class_name: str,
    init_args: MappingProxyType[str, inspect.Parameter],
    kwarg_splat: str,
) -> list[str]: ...
```

Builds the exact list of lines inserted for a generated `__repr__`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `class_name` | `str` | — | Name used in the generated docstring. |
| `init_args` | `MappingProxyType[str, inspect.Parameter]` | — | Constructor parameter mapping returned by `inspect.signature`. |
| `kwarg_splat` | `str` | — | Placeholder text used when a `VAR_KEYWORD` parameter is present. |

Return type: `list[str]`

Example:

```python
lines = create_repr_lines("Account", init_args, kwarg_splat="kwargs=...")
```

### `create_repr`

Import path: `from crepr.crepr import create_repr`

Signature:

```python
def create_repr(
    module: ModuleType,
    kwarg_splat: str,
    ignore_existing: bool,
) -> dict[int, Change]: ...
```

Builds a line-number-indexed change map for every eligible class in the module.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `module` | `ModuleType` | — | Loaded module to scan. |
| `kwarg_splat` | `str` | — | Placeholder fragment for `**kwargs`. |
| `ignore_existing` | `bool` | — | When `True`, skip classes that already define `__repr__`. |

Return type: `dict[int, Change]`

Example:

```python
changes = create_repr(module, kwarg_splat="{}", ignore_existing=True)
```

### `remove_repr`

Import path: `from crepr.crepr import remove_repr`

Signature:

```python
def remove_repr(module: ModuleType) -> dict[int, Change]: ...
```

Builds a deletion-oriented change map by recovering existing `__repr__` source from each eligible class.

## Mutation Functions

### `insert_changes`

Import path: `from crepr.crepr import insert_changes`

Signature:

```python
def insert_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]: ...
```

Starts from the module source and inserts the `Change["lines"]` blocks at each line number, processing from bottom to top.

### `remove_changes`

Import path: `from crepr.crepr import remove_changes`

Signature:

```python
def remove_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]: ...
```

Deletes the exact lines described by each change block, also in reverse order.

### `print_changes`

Import path: `from crepr.crepr import print_changes`

Signature:

```python
def print_changes(changes: dict[int, Change], action: str) -> None: ...
```

Prints a label such as `__repr__ generated for class: Account` followed by the associated source lines.

### `print_diff`

Import path: `from crepr.crepr import print_diff`

Signature:

```python
def print_diff(before: list[str], after: list[str]) -> None: ...
```

Prints a unified diff with line colors handled by `typer.secho`.

### `apply_changes`

Import path: `from crepr.crepr import apply_changes`

Signature:

```python
def apply_changes(
    module: ModuleType,
    changes: dict[int, Change],
    file_path: pathlib.Path,
    diff: bool,
    change_func: Callable[[ModuleType, dict[int, Change]], list[str]],
) -> None: ...
```

Runs either insertion or deletion, then chooses between diff output and file writing.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `module` | `ModuleType` | — | Loaded module whose source will be transformed. |
| `changes` | `dict[int, Change]` | — | Change map keyed by source line number. |
| `file_path` | `pathlib.Path` | — | Path written in inline mode. |
| `diff` | `bool` | — | `True` prints a diff, `False` writes the file. |
| `change_func` | `Callable[[ModuleType, dict[int, Change]], list[str]]` | — | Either `insert_changes` or `remove_changes`. |

Return type: `None`

Example:

```python
apply_changes(
    module,
    changes,
    Path("models.py"),
    diff=True,
    change_func=insert_changes,
)
```

## Common Combination Pattern

Programmatic add flow:

```python
from pathlib import Path
from crepr.crepr import apply_changes, create_repr, get_module, insert_changes

path = Path("models.py")
module = get_module(path)
changes = create_repr(module, kwarg_splat="kwargs=...", ignore_existing=True)

apply_changes(module, changes, path diff=True, change_func=insert_changes)
```

Programmatic remove flow:

```python
from pathlib import Path
from crepr.crepr import apply_changes, get_module, remove_changes, remove_repr

path = Path("models.py")
module = get_module(path)
changes = remove_repr(module)

apply_changes(module, changes, path diff=False, change_func=remove_changes)
```

These combinations are the same primitives the CLI commands use internally.
