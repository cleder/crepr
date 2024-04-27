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
from collections.abc import Iterable
from types import MappingProxyType
from types import ModuleType
from typing import Annotated
from typing import TypedDict

import typer

app = typer.Typer(no_args_is_help=True)


class Change(TypedDict):
    """A dictionary representing a change to be made to the source code."""

    class_name: str
    lines: list[str]


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
    if "__init__" in cls.__dict__:
        init_method = cls.__init__  # type: ignore[misc]
        init_source = inspect.getsource(init_method)
        init_line_number = inspect.findsource(init_method)[1]
        return init_source, init_line_number
    return "", -1


def get_init_args(
    cls: type,
) -> tuple[str, MappingProxyType[str, inspect.Parameter] | None, int, str | None]:
    """Get the __init__ arguments of a class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        tuple[str, MappingProxyType[str, inspect.Parameter] | None]:
        A tuple containing the class name and the dictionary of __init__ arguments,
        or None if the class does not have an __init__ method.

    """
    if "__init__" in cls.__dict__:
        init_source, lineno = get_init_source(cls)
        init_method = cls.__init__  # type: ignore[misc]
        init_signature = inspect.signature(init_method)
        init_args = init_signature.parameters
        return cls.__name__, init_args, lineno, init_source
    return cls.__name__, None, -1, None


def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool:
    """Check if the given init_args dictionary contains only keyword arguments.

    Returns
    -------
        bool: True if the init_args only contain keyword arguments, False otherwise.

    """
    if not init_args:
        return False
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
    if not has_only_kwargs(init_args):
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
            else f"            f'**{arg_name}={kwarg_splat},'"
        )
        for arg_name, arg_param in init_args.items()
        if arg_name != "self"
    )
    lines.extend(("        ')')", ""))
    return lines


def get_class_objects(file_path: str) -> Iterable[tuple[type, ModuleType]]:
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
        loader = importlib.machinery.SourceFileLoader(uuid.uuid4().hex, file_path)
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
    for _, obj in inspect.getmembers(module, inspect.isclass):
        yield (obj, module)


def apply_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]:
    """Apply the changes to the source code of the given module.

    Args:
    ----
        module (ModuleType): The module to modify.
        changes (dict[int, Change]): The changes to apply.

    """
    src = inspect.getsource(module).splitlines()
    for lineno in sorted(changes.keys(), reverse=True):
        for i, change in enumerate(changes[lineno]["lines"]):
            src.insert(lineno + i, change)
    return src


def print_changed(module: ModuleType, changes: dict[int, Change]) -> None:
    """Print out the changes made to the source code.

    Inserts the given changes into the source code of the given module
    and prints the modified source code.

    """
    src = apply_changes(module, changes)
    typer.echo("\n".join(src))


def create(file_path: str, kwarg_splat: str) -> tuple[ModuleType, dict[int, Change]]:
    """Create a __repr__ method for each class of a python file."""
    classes_processed = 0
    changes: dict[int, Change] = {}
    module = None
    for obj, module in get_class_objects(file_path):
        if not is_class_in_module(obj, module):
            continue
        class_name, init_args, lineno, source = get_init_args(obj)
        if not init_args:
            continue
        assert init_args is not None  # noqa: S101
        new_lines = create_repr_lines(class_name, init_args, kwarg_splat)
        assert source is not None  # noqa: S101
        end_line = len(source.splitlines()) + lineno
        changes[end_line] = {"lines": new_lines, "class_name": class_name}
        classes_processed += 1
    if not classes_processed:
        typer.secho(
            f"Error: No __repr__ could be generated for '{file_path}'.",
            fg="red",
        )
        raise typer.Exit(code=1)
    assert module is not None  # noqa: S101
    return module, changes


file_arg = typer.Argument(help="The python source file")
splat_option = typer.Option(
    help="The **kwarg splat",
)


@app.command()
def show(
    file_path: Annotated[str, file_arg],
    kwarg_splat: Annotated[str, splat_option] = "...",
) -> None:
    """Show what changes would be made to the source code."""
    module, changes = create(file_path, kwarg_splat)
    print_changed(module, changes)


@app.command()
def diff(
    file_path: Annotated[str, file_arg],
    kwarg_splat: Annotated[str, splat_option] = "...",
) -> None:
    """Show the diff of the changes to be made to the source code."""
    module, changes = create(file_path, kwarg_splat)
    after = apply_changes(module, changes)
    before = inspect.getsource(module).splitlines()
    diff = difflib.unified_diff(before, after, lineterm="")
    typer.echo("\n".join(diff))


@app.command()
def write(
    file_path: Annotated[str, file_arg],
    kwarg_splat: Annotated[str, splat_option] = "...",
) -> None:
    """Write the changes to the source code."""
    module, changes = create(file_path, kwarg_splat)
    src = apply_changes(module, changes)
    with pathlib.Path(file_path).open(mode="w", encoding="UTF-8") as f:
        f.write("\n".join(src))


if __name__ == "__main__":
    app()

__all__ = ["create"]
