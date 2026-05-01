---
title: "CLI Commands"
description: "Reference the add and remove commands, their signatures, options, defaults, and command-line usage patterns."
---

The main user-facing API of `crepr` is its Typer CLI. The console script is registered in `pyproject.toml` as `crepr = "crepr.crepr:app"`, and the two public commands are `add` and `remove`.

## `add`

Source file: `crepr/crepr.py`

Import path: `from crepr.crepr import add`

Signature:

```python
def add(
    files: Annotated[list[pathlib.Path], file_arg],
    kwarg_splat: Annotated[str, splat_option] = "{}",
    diff: Annotated[Optional[bool], diff_inline_option] = None,
    ignore_existing: Annotated[bool, ignore_existing_option] = False,
) -> None: ...
```

Adds generated `__repr__` methods to all eligible classes in one or more files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `list[pathlib.Path]` | — | One or more Python source files to inspect. |
| `kwarg_splat` | `str` | `"{}"` | Placeholder string emitted for `**kwargs`. |
| `diff` | `Optional[bool]` | `None` | `None` prints only the generated block, `True` shows a diff, `False` writes inline. |
| `ignore_existing` | `bool` | `False` | When `True`, add another generated `__repr__` even if one already exists. |

Return type: `None`

CLI examples:

```bash
crepr add models.py
crepr add models.py --diff
crepr add models.py --inline
crepr add models.py --kwarg-splat "kwargs=..."
crepr add models.py --ignore-existing --diff
```

Behavior notes:

- With no mode flag, `add` calls `print_changes`.
- With `--diff`, `add` calls `apply_changes(..., change_func=insert_changes)` in diff mode.
- With `--inline`, `add` calls the same helper in write mode.
- The command loops over all files from `get_modules`, so broken files are skipped rather than aborting the whole batch.

## `remove`

Source file: `crepr/crepr.py`

Import path: `from crepr.crepr import remove`

Signature:

```python
def remove(
    files: Annotated[list[pathlib.Path], file_arg],
    diff: Annotated[Optional[bool], diff_inline_option] = None,
) -> None: ...
```

Removes `__repr__` methods from eligible classes in one or more files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | `list[pathlib.Path]` | — | One or more Python source files to inspect. |
| `diff` | `Optional[bool]` | `None` | `None` previews removals, `True` shows a diff, `False` writes inline. |

Return type: `None`

CLI examples:

```bash
crepr remove models.py
crepr remove models.py --diff
crepr remove models.py --inline
```

## Common Usage Patterns

### Preview first

```bash
crepr add src/models.py
crepr remove src/models.py
```

Useful when you want the method text itself, not a patch.

### Diff in review workflows

```bash
crepr add src/models.py --diff
```

Useful in code review, CI logs, or pre-commit diagnostics because the output is a unified diff.

### Inline after review

```bash
crepr add src/models.py --inline
```

Useful when you want `crepr` to act as the final mutating step after the diff looked correct.

## Relationship To The Internal API

`add` and `remove` are thin orchestration layers. They do not implement inspection or mutation directly. Instead they call:

- `get_modules` for file loading
- `create_repr` or `remove_repr` for change-map construction
- `print_changes` or `apply_changes` for output mode handling

That is why the CLI is easy to reason about: each command mostly wires together smaller functions already documented on the other API pages.
