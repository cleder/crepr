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
from collections.abc import Iterator
from types import MappingProxyType
from types import ModuleType
from typing import Annotated
from typing import Optional
from typing import TypedDict

import typer

app = typer.Typer(no_args_is_help=True)


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
        typer.secho(f"Error: File '{file_path}' not found.", fg="red")
        raise typer.Exit(code=1) from e
    except ImportError as e:
        typer.secho(f"Error: Could not import '{file_path}'.", fg="red")
        raise typer.Exit(code=1) from e
    except SyntaxError as e:
        typer.secho(f"Error: Could not parse '{file_path}'.", fg="red")
        raise typer.Exit(code=1) from e
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
    file_path: pathlib.Path,
    kwarg_splat: str,
) -> tuple[ModuleType, dict[int, Change]]:
    """Create a __repr__ method for each class of a python file."""
    changes: dict[int, Change] = {}
    module = get_module(file_path)
    for obj, init_args, lineno, source in get_all_init_args(module):
        new_lines = create_repr_lines(obj.__name__, init_args, kwarg_splat)
        changes[lineno + len(source)] = {
            "lines": new_lines,
            "class_name": obj.__name__,
        }
    return module, changes


def remove_repr(file_path: pathlib.Path) -> tuple[ModuleType, dict[int, Change]]:
    """Remove the __repr__ method for each class of a python file."""
    changes: dict[int, Change] = {}
    module = get_module(file_path)
    for obj, _, _, _ in get_all_init_args(module):
        lines_to_remove, lineno = get_repr_source(obj)
        changes[lineno] = {
            "lines": lines_to_remove.splitlines(),
            "class_name": obj.__name__,
        }
    return module, changes


@app.command()
def add(
    files: Annotated[list[pathlib.Path], file_arg],
    kwarg_splat: Annotated[str, splat_option] = "{}",
    diff: Annotated[Optional[bool], diff_inline_option] = None,  # noqa: UP007
) -> None:
    """Add __repr__ to all classes in the source code."""
    for file_path in files:
        module, changes = create_repr(file_path, kwarg_splat)
        if not changes:
            continue
        src = insert_changes(module, changes)
        if diff is None:
            typer.echo("\n".join(src))
        elif diff:
            before = inspect.getsource(module).splitlines()
            _diff = difflib.unified_diff(before, src, lineterm="")
            typer.echo("\n".join(_diff))
            continue
        else:
            with file_path.open(mode="w", encoding="UTF-8") as f:
                f.write("\n".join(src))


@app.command()
def remove(
    files: Annotated[list[pathlib.Path], file_arg],
    diff: Annotated[Optional[bool], diff_inline_option] = None,  # noqa: UP007
) -> None:
    """Remove the __repr__ method from all classes in the source code."""
    for file_path in files:
        module, changes = remove_repr(file_path)
        if not changes:
            continue
        src = remove_changes(module, changes)
        if diff is None:
            typer.echo("\n".join(src))
        elif diff:
            before = inspect.getsource(module).splitlines()
            _diff = difflib.unified_diff(before, src, lineterm="")
            typer.echo("\n".join(_diff))
            continue
        else:
            with file_path.open(mode="w", encoding="UTF-8") as f:
                f.write("\n".join(src))


@app.command()
def report_missing(files: Annotated[list[pathlib.Path], file_arg]) -> None:
    """Count and print classes without a __repr__ method in the source code."""
    for file_path in files:
        try:
            process_file(file_path)
        except FileNotFoundError:
            typer.secho(f"File '{file_path}' not found.", fg="red")
        except ImportError as e:
            error_message = f"Error importing module from '{file_path}': {str(e)}"
            typer.secho(error_message, fg="red")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            typer.secho(error_message, fg="red")


def process_file(file_path: pathlib.Path) -> None:
    """Process a single file and report classes without a __repr__ method."""
    module = load_module(file_path)
    classes = extract_classes(module, file_path)
    no_repr_classes = filter_no_repr(classes)
    report_results(file_path, classes, no_repr_classes)


def load_module(file_path: pathlib.Path) -> ModuleType:
    """Load a module from a given file path."""
    try:
        return get_module(file_path)
    except ImportError as e:
        error_message = f"Failed to load module from {file_path}: {str(e)}"
        raise ImportError(error_message) from None


def extract_classes(module: ModuleType, file_path: pathlib.Path) -> list[type]:
    """Extract classes from a module."""
    try:
        return [
            obj for _, obj in inspect.getmembers(module, inspect.isclass)
            if is_class_in_module(obj, module)
        ]
    except AttributeError as e:
        error_message = f"Error processing classes in {file_path}: {str(e)}"
        raise AttributeError(error_message) from None


def filter_no_repr(classes: list[type]) -> list[str]:
    """Filter out classes without a __repr__ method."""
    return [
        obj.__name__ for obj in classes
        if get_repr_source(obj)[1] == -1
    ]


def report_results(file_path: pathlib.Path, classes: list[type], no_repr_classes: list[str]) -> None:
    """Report the results of classes without a __repr__ method."""
    if no_repr_classes:
        typer.secho(
            f"In module '{file_path}': {len(no_repr_classes)} class(es) "
            "don't have a __repr__ method:",
            fg="yellow"
        )
        for class_name in no_repr_classes:
            typer.echo(f"{file_path}: {class_name}")
    else:
        typer.secho(
            f"All {len(classes)} class(es) in module '{file_path}' "
            "have a __repr__ method.",
            fg="green"
        )

if __name__ == "__main__":
    app()

