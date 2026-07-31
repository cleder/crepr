---
title: "Package Exports"
description: "Reference the package-level exports, module constants, and public data structures exposed by crepr."
---

This page covers the objects that define the top-level identity of `crepr`: the package export, the Typer application, the public exception type, the `Change` structure, and the module-level option objects used by the CLI command signatures.

## Package Export

Source file: `crepr/__init__.py`

### `__version__`

Import path: `from crepr import __version__`

Definition:

```python
__version__ = "0.6.0dev0"
```

The package root only re-exports `__version__` from `crepr/about.py`. If you need the installed library version in tooling or diagnostics, this is the stable import path.

Example:

```python
from crepr import __version__

print(__version__)
```

## CLI Application Object

Source file: `crepr/crepr.py`

### `app`

Import path: `from crepr.crepr import app`

Definition:

```python
app = typer.Typer(no_args_is_help=True)
```

`app` is the Typer application registered as the console entry point in `pyproject.toml` through `crepr = "crepr.crepr:app"`. The `no_args_is_help=True` configuration means invoking the command with no subcommand shows help instead of silently doing nothing.

Example:

```python
from crepr.crepr import app

# Useful when embedding crepr into another Typer-based tool.
print(app.registered_commands)
```

## Public Classes And Types

Source file: `crepr/crepr.py`

### `CreprError`

Import path: `from crepr.crepr import CreprError`

Signature:

```python
class CreprError(Exception):
    def __init__(self: Self, message: str, exit_code: int = 1) -> None: ...
```

Use `CreprError` when calling inspection helpers programmatically. The CLI catches it inside `get_modules`, but Python integrations can catch it directly and read the `message` and `exit_code` attributes.

Constructor parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | — | Human-readable error message shown to the user. |
| `exit_code` | `int` | `1` | Exit status the CLI should use for that error. |

Example:

```python
from pathlib import Path
from crepr.crepr import CreprError, get_module

try:
    get_module(Path("broken.py"))
except CreprError as exc:
    print(exc.message)
```

### `Change`

Import path: `from crepr.crepr import Change`

Definition:

```python
class Change(TypedDict):
    class_name: str
    lines: list[str]
```

`Change` is the normalized editing payload shared by generation, removal, preview, and file mutation helpers. Each change map is keyed by a source line number and stores the target class name plus the lines to insert or remove.

Example:

```python
from crepr.crepr import Change

change: Change = {
    "class_name": "Account",
    "lines": ["", "    def __repr__(self) -> str:", "        ..."],
}
```

## Public Option Objects

These values are mostly useful if you are reading or extending the command signatures directly.

### `file_arg`

Import path: `from crepr.crepr import file_arg`

Definition:

```python
file_arg = typer.Argument(help="The python source file(s)")
```

### `splat_option`

Import path: `from crepr.crepr import splat_option`

Definition:

```python
splat_option = typer.Option(help="The **kwarg splat")
```

### `diff_inline_option`

Import path: `from crepr.crepr import diff_inline_option`

Definition:

```python
diff_inline_option = typer.Option(
    "--diff/--inline",
    help="Display the diff / Apply changes to the file(s)",
)
```

### `ignore_existing_option`

Import path: `from crepr.crepr import ignore_existing_option`

Definition:

```python
ignore_existing_option = typer.Option(
    "--ignore-existing",
    help="Add __repr__ regardless if one exists",
    is_flag=True,
)
```

These objects are not the main end-user API, but documenting them makes the command signatures on the next pages easier to read and trace back to source.
