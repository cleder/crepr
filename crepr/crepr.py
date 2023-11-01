"""
Create a ``__repr__`` for your python classes.

A Python script that takes a module name as a command-line argument,
imports the specified module, and then prints a ``__repr__`` method
for each class defined in the module.
It uses the definition found in the  ``__init__`` method of the class.
"""
import importlib
import inspect
from types import MappingProxyType
from types import ModuleType

import typer

app = typer.Typer()


def get_init_args(
    cls: type,
) -> tuple[str | None, MappingProxyType[str, inspect.Parameter] | None]:
    """
    Get the __init__ arguments of a class.

    Args:
    ----
        cls (type): The class to inspect.

    Returns:
    -------
        tuple[str | None, MappingProxyType[str, inspect.Parameter] | None]:
        A tuple containing the class name and the dictionary of __init__ arguments,
        or None if the class does not have an __init__ method.
    """
    if "__init__" in cls.__dict__:
        init_method = cls.__init__  # type: ignore[misc]
        init_signature = inspect.signature(init_method)
        init_args = init_signature.parameters
        return cls.__name__, init_args
    return None, None


def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool:
    """
    Check if the given init_args dictionary contains only keyword arguments.

    Returns
    -------
        bool: True if the init_args only contain keyword arguments, False otherwise.
    """
    return any(
        param.kind  # type: ignore[comparison-overlap]
        not in ["POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY"]
        for arg_name, param in init_args.items()
        if arg_name != "self"
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


def print_repr(
    class_name: str,
    init_args: MappingProxyType[str, inspect.Parameter],
) -> None:
    """Print the __repr__ method for a class."""
    if not has_only_kwargs(init_args):
        typer.echo(f"Skipping {class_name} due to positional arguments.")
        return
    typer.echo(f"Class: {class_name}")
    typer.echo("    def __repr__(self) -> str:")
    typer.echo("        return (f'{self.__class__.__name__}('")
    for arg_name in init_args:
        if arg_name == "self":
            continue
        typer.echo(f"            f'{arg_name}={{self.{arg_name}!r}}, '")
    typer.echo("        ')')")
    typer.echo()


@app.command()  # type: ignore[misc]
def create(module_name: str) -> None:
    """
    Create a __repr__ method for each class in a specified module.

    Args:
    ----
        module_name (str): The name of the module to process.

    Returns:
    -------
        None
    """
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        typer.echo(f"Error: Module '{module_name}' not found.")
        return
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if not is_class_in_module(obj, module):
            continue
        class_name, init_args = get_init_args(obj)
        if not class_name:
            continue

        assert init_args is not None  # noqa: S101
        print_repr(class_name, init_args)


if __name__ == "__main__":
    app()

__all__ = ["create"]
