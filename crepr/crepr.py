"""
Create a ``__repr__`` for your python classes.

A Python script that takes a module name as a command-line argument,
imports the specified module, and then prints a ``__repr__`` method
for each class defined in the module.
It uses the definition found in the  ``__init__`` method of the class.
"""
import importlib
import inspect
from collections.abc import Iterable
from types import MappingProxyType
from types import ModuleType

import typer

app = typer.Typer()


def get_init_args(
    cls: type,
) -> tuple[str, MappingProxyType[str, inspect.Parameter] | None]:
    """
    Get the __init__ arguments of a class.

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
        init_method = cls.__init__  # type: ignore[misc]
        init_signature = inspect.signature(init_method)
        init_args = init_signature.parameters
        return cls.__name__, init_args
    return cls.__name__, None


def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool:
    """
    Check if the given init_args dictionary contains only keyword arguments.

    Returns
    -------
        bool: True if the init_args only contain keyword arguments, False otherwise.
    """
    if not init_args:
        return False
    return all(
        param.kind
        in {
            inspect._ParameterKind.POSITIONAL_OR_KEYWORD,  # noqa: SLF001
            inspect._ParameterKind.KEYWORD_ONLY,  # noqa: SLF001
        }
        for param in init_args.values()
    )


def is_class_in_module(cls: type, module: ModuleType) -> bool:
    """
    Check if a class is defined in a specific module.

    Args:
    ----
        cls (type): The class to check.
        module (ModuleType): The module to compare against.

    Returns:
    -------
        bool: True if the class is defined in the specified module, False otherwise.
    """
    return inspect.getmodule(cls) == module


def create_repr_lines(
    class_name: str,
    init_args: MappingProxyType[str, inspect.Parameter],
) -> list[str]:
    """Create the source loc for the __repr__ method for a class."""
    if not has_only_kwargs(init_args):
        typer.echo(f"Skipping {class_name} due to positional arguments.")
        return []
    lines = [
        f"#  Class: {class_name}",
        "    def __repr__(self) -> str:",
        "        return (f'{self.__class__.__name__}('",
    ]
    lines.extend(
        f"            f'{arg_name}={{self.{arg_name}!r}}, '"
        for arg_name in init_args
        if arg_name != "self"
    )
    lines.append("        ')')")
    return lines


def print_repr(lines: Iterable[str]) -> None:
    """Print the source loc for the __repr__ method for a class."""
    for line in lines:
        typer.echo(line)


def get_class_objects(module_name: str) -> Iterable[tuple[type, ModuleType]]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        typer.echo(f"Error: Module '{module_name}' not found.")
        return
    for _, obj in inspect.getmembers(module, inspect.isclass):
        yield (obj, module)


@app.command()
def create(module_name: str) -> None:
    """Create a __repr__ method for each class in a specified module."""
    classes_processed = 0
    for obj, module in get_class_objects(module_name):
        if not is_class_in_module(obj, module):
            continue
        class_name, init_args = get_init_args(obj)
        if not init_args:
            continue
        assert init_args is not None  # noqa: S101
        print_repr(create_repr_lines(class_name, init_args))
        classes_processed += 1
    if not classes_processed:
        typer.secho(f"Error: No classes found in module '{module_name}'.", fg="red")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()  # pragma: no cover

__all__ = ["create"]
