"""Create a ``__repr__`` for your python classes.

A Python script that takes a file name as a command-line argument,
imports the specified module, and then prints a ``__repr__`` method
for each class defined in the module.
It uses the definition found in the  ``__init__`` method of the class.
"""

import difflib
import importlib
import importlib.machinery
import inspect
import pathlib
import uuid
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from types import MappingProxyType
from types import ModuleType
from typing import Annotated
from typing import Optional
from typing import Self
from typing import TypedDict

import typer

app = typer.Typer(no_args_is_help=True)


class CreprError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self: Self, message: str, exit_code: int = 1) -> None:
        """Initialize the exception with a message and an optional exit code."""
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class Change(TypedDict):
    """A dictionary representing a change to be made to the source code."""

    class_name: str
    lines: list[str]


file_arg = typer.Argument(help="The python source file(s)")
splat_option = typer.Option(help="The **kwarg splat")
diff_inline_option = typer.Option(
    "--diff/--inline",
    help="Display the diff / Apply changes to the file(s)",
)
ignore_existing_option = typer.Option(
    "--ignore-existing",
    help="Add __repr__ regardless if one exists",
    is_flag=True,
)


def get_method_source(cls: type, method_name: str) -> tuple[str, int]:
    """Get the source code and line number of a method of a class.

    Args:
    ----
        cls (type): The class to inspect.
        method_name (str): The name of the method to get the source code of.

    Returns:
    -------
        tuple[str, int]: A tuple containing the source code of the method and
        the line number where it was found, or an empty string and -1 if the class
        does not have the specified method.

    """
    if method_name not in cls.__dict__:
        return "", -1
    method = cls.__dict__[method_name]
    try:
        method_source = inspect.getsource(method)
        method_line_number = inspect.findsource(method)[1]
    except OSError:
        return "", -1
    else:
        return method_source, method_line_number


def get_init_source(cls: type) -> tuple[str, int]:
    """Get the source code and line number of the __init__ method of a class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        tuple[str, int]: A tuple containing the source code of the __init__ method and
        the line number where it was found, or an empty string and -1 if the class
        does not have an __init__ method.

    """
    return get_method_source(cls, "__init__")


def get_repr_source(cls: type) -> tuple[str, int]:
    """Get the source code and line number of the __repr__ method of a class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        tuple[str, int]: A tuple containing the source code of the __repr__ method and
        the line number where it was found, or an empty string and -1 if the class
        does not have an __repr__ method.

    """
    return get_method_source(cls, "__repr__")


def get_init_args(
    cls: type,
) -> tuple[MappingProxyType[str, inspect.Parameter] | None, int, list[str]]:
    """Get the __init__ arguments of a class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        tuple[str, MappingProxyType[str, inspect.Parameter] | None, str]:
        A tuple containing a dictionary of __init__ arguments, or None if the class
        does not have an __init__ method, the line number of the __init_method,
        and the source code lines of the __init__ method.

    """
    if "__init__" in cls.__dict__:
        init_source, lineno = get_init_source(cls)
        init_method = cls.__init__  # type: ignore[misc]
        init_signature = inspect.signature(init_method)
        init_args = init_signature.parameters
        return init_args, lineno, init_source.splitlines()
    return None, -1, []


def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool:
    """Check if the given init_args dictionary contains only keyword arguments.

    Returns
    -------
        bool: True if the init_args only contain keyword arguments, False otherwise.

    """
    return all(
        param.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        }
        for param in init_args.values()
    )


def is_class_in_module(cls: type, module: ModuleType) -> bool:
    """Check if a class is defined in a specific module.

    Args:
    ----
        cls (type): The class to check.
        module (ModuleType): The module to compare against.

    Returns:
    -------
        bool: True if the class is defined in the specified module,
              False if it is imported.

    """
    return inspect.getmodule(cls) == module


def repr_exists(cls: type) -> bool:
    """Check if a __repr__ method already exists in the class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        bool: True if the __repr__ method exists, False otherwise.

    """
    return "__repr__" in cls.__dict__


def create_repr_lines(
    class_name: str,
    init_args: MappingProxyType[str, inspect.Parameter],
    kwarg_splat: str,
) -> list[str]:
    """Create the source loc for the __repr__ method for a class."""
    if not init_args:
        return []
    lines = [
        "",
        "    def __repr__(self) -> str:",
        f'        """Create a string (c)representation for {class_name}."""',
        "        return (f'{self.__class__.__module__}.{self.__class__.__name__}('",
    ]
    lines.extend(
        (
            f"            f'{arg_name}={{self.{arg_name}!r}}, '"
            if arg_param.kind != inspect.Parameter.VAR_KEYWORD
            else f"            f'**{kwarg_splat},'"
        )
        for arg_name, arg_param in init_args.items()
        if arg_name != "self"
    )
    lines.extend(("        ')')", ""))
    return lines


def get_module(file_path: pathlib.Path) -> ModuleType:
    """Get all classes of a source file.

    Given a file path, loads the module and yields all classes defined in it
    along with the module object.

    Args:
    ----
        file_path (str): The path to the file containing the module.

    Yields:
    ------
        tuple[type, ModuleType]: A tuple containing the class and the module objects.

    """
    try:
        loader = importlib.machinery.SourceFileLoader(uuid.uuid4().hex, str(file_path))
        module = loader.load_module()
    except FileNotFoundError as e:
        message = f"Error: File '{file_path}' not found."
        raise CreprError(message, exit_code=1) from e
    except ImportError as e:
        message = f"Error: Could not import '{file_path}'."
        raise CreprError(message, exit_code=1) from e
    except SyntaxError as e:
        message = f"Error: Could not parse '{file_path}'."
        raise CreprError(message, exit_code=1) from e
    return module


def insert_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]:
    """Apply the changes to the source code of the given module.

    Args:
    ----
        module (ModuleType): The module to modify.
        changes (dict[int, Change]): The changes to apply.

    """
    src = inspect.getsource(module).splitlines()
    for lineno, change in sorted(changes.items(), reverse=True):
        for i, line in enumerate(change["lines"]):
            src.insert(lineno + i, line)
    return src


def remove_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]:
    """Apply the changes to the source code of the given module.

    Args:
    ----
        module (ModuleType): The module to modify.
        changes (dict[int, Change]): The changes to apply.

    """
    src = inspect.getsource(module).splitlines()
    for lineno, change in sorted(changes.items(), reverse=True):
        for line in change["lines"]:
            assert src[lineno] == line  # noqa: S101
            del src[lineno]
    return src


def get_all_init_args(
    module: ModuleType,
) -> Iterator[tuple[type, MappingProxyType[str, inspect.Parameter], int, list[str]]]:
    """Get the __init__ arguments of all classes in a module.

    Args:
    ----
        module (ModuleType): The module to inspect.

    Returns:
    -------
        Iterator[tuple[MappingProxyType[str, inspect.Parameter], int, list[str]]]:
        An iterator of tuples containing a dictionary of __init__ arguments,
        the line number of the __init_method, and the source code lines of the __init__
        method.

    """
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if not is_class_in_module(obj, module):
            continue
        init_args, lineno, source = get_init_args(obj)
        if not init_args or lineno == -1 or not has_only_kwargs(init_args):
            continue
        yield obj, init_args, lineno, source


def create_repr(
    module: ModuleType,
    kwarg_splat: str,
    ignore_existing: bool = False,  # noqa: FBT001 FBT002
) -> dict[int, Change]:
    """Create a __repr__ method for each class of a python file."""
    changes: dict[int, Change] = {}
    for obj, init_args, lineno, source in get_all_init_args(module):
        if repr_exists(obj) and ignore_existing:
            continue
        new_lines = create_repr_lines(obj.__name__, init_args, kwarg_splat)
        changes[lineno + len(source)] = {
            "lines": new_lines,
            "class_name": obj.__name__,
        }
    return changes


def remove_repr(module: ModuleType) -> dict[int, Change]:
    """Remove the __repr__ method for each class of a python file."""
    changes: dict[int, Change] = {}
    for obj, _, _, _ in get_all_init_args(module):
        lines_to_remove, lineno = get_repr_source(obj)
        changes[lineno] = {
            "lines": lines_to_remove.splitlines(),
            "class_name": obj.__name__,
        }
    return changes


def get_modules(
    files: Iterable[pathlib.Path],
) -> Iterator[tuple[ModuleType, pathlib.Path]]:
    """Iterate over all files and return the loaded module."""
    for file_path in files:
        try:
            module = get_module(file_path)
        except CreprError as e:
            typer.secho(e.message, fg="red", err=True)
            continue
        yield module, file_path


def print_changes(changes: dict[int, Change], action: str) -> None:
    """Print changes for each class."""
    for change in changes.values():
        typer.echo(f"__repr__ {action} for class: {change['class_name']}")
        typer.echo("\n".join(change["lines"]))
        typer.echo("")


def apply_changes(
    module: ModuleType,
    changes: dict[int, Change],
    file_path: pathlib.Path,
    diff: bool,  # noqa: FBT001
    change_func: Callable[[ModuleType, dict[int, Change]], list[str]],
) -> None:
    """Apply changes to the module and handle diff or file writing."""
    src = change_func(module, changes)
    if diff:
        before = inspect.getsource(module).splitlines()
        _diff = difflib.unified_diff(before, src, lineterm="")
        typer.echo("\n".join(_diff))
    else:
        with file_path.open(mode="w", encoding="UTF-8") as f:
            f.write("\n".join(src))


@app.command()
def add(
    files: Annotated[list[pathlib.Path], file_arg],
    kwarg_splat: Annotated[str, splat_option] = "{}",
    diff: Annotated[Optional[bool], diff_inline_option] = None,  # noqa: UP007
    ignore_existing: Annotated[bool, ignore_existing_option] = False,  # noqa: FBT002
) -> None:
    """Add __repr__ to all classes in the source code."""
    for module, file_path in get_modules(files):
        changes = create_repr(module, kwarg_splat, ignore_existing)
        if not changes:
            continue

        if diff is None:
            print_changes(changes, "generated")
        else:
            apply_changes(
                module, changes, file_path, diff=diff, change_func=insert_changes,
            )


@app.command()
def remove(
    files: Annotated[list[pathlib.Path], file_arg],
    diff: Annotated[Optional[bool], diff_inline_option] = None,  # noqa: UP007
) -> None:
    """Remove the __repr__ method from all classes in the source code."""
    for module, file_path in get_modules(files):
        changes = remove_repr(module)
        if not changes:
            continue

        if diff is None:
            print_changes(changes, "removed")
        else:
            apply_changes(
                module, changes, file_path, diff=diff, change_func=remove_changes,
            )


@app.command()
def report_missing(
    files: Annotated[list[pathlib.Path], file_arg],
) -> None:
    """Report classes without __repr__ methods."""
    for module, file_path in get_modules(files):
        report_missing_classes(module, file_path)


def report_missing_classes(module: ModuleType, file_path: pathlib.Path) -> None:
    """Report classes missing a __repr__ method in the specified module.

    Args:
        module (ModuleType): The module to inspect for classes.
        file_path (pathlib.Path): File path for the class.

    """
    for obj, _, lineno, _ in get_all_init_args(module):
        repr_method = inspect.getattr_static(obj, "__repr__", None)
        if repr_method is None or repr_method is object.__repr__:
            typer.echo(f"{file_path}: {lineno}: {obj.__name__}")


if __name__ == "__main__":
    app()
