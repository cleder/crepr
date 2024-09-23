import difflib
import importlib
import importlib.machinery
import inspect
import pathlib
import uuid
from collections.abc import Iterable
from types import MappingProxyType, ModuleType
from typing import Annotated, Iterator, List, Optional, Self, Type, TypedDict

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


def get_method_source(cls: type, method_name: str) -> tuple[str, int]:
    """Get the source code and line number of a method of a class."""
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
    """Get the source code and line number of the __init__ method of a class."""
    return get_method_source(cls, "__init__")


def get_repr_source(cls: type) -> tuple[str, int]:
    """Get the source code and line number of the __repr__ method of a class."""
    return get_method_source(cls, "__repr__")


def get_init_args(
    cls: type,
) -> tuple[MappingProxyType[str, inspect.Parameter] | None, int, list[str]]:
    """Get the __init__ arguments of a class."""
    if "__init__" in cls.__dict__:
        init_source, lineno = get_init_source(cls)
        init_method = cls.__init__  # type: ignore[misc]
        init_signature = inspect.signature(init_method)
        init_args = init_signature.parameters
        return init_args, lineno, init_source.splitlines()
    return None, -1, []


def has_only_kwargs(init_args: MappingProxyType[str, inspect.Parameter]) -> bool:
    """Check if the given init_args dictionary contains only keyword arguments."""
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
    """Check if a class is defined in a specific module."""
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
        '        """Create a string (c)representation for {}."""'.format(class_name),
        "        return (f'{self.__class__.__module__}.{self.__class__.__name__}('",
    ]
    lines.extend(
        (
            "            f'{arg_name}={{self.{arg_name}!r}}, '"
            if arg_param.kind != inspect.Parameter.VAR_KEYWORD
            else "            f'**{},'"
        ).format(arg_name, kwarg_splat)
        for arg_name, arg_param in init_args.items()
        if arg_name != "self"
    )
    lines.extend(("        ')')", ""))
    return lines


def get_module(file_path: pathlib.Path) -> ModuleType:
    """Get all classes of a source file."""
    try:
        loader = importlib.machinery.SourceFileLoader(uuid.uuid4().hex, str(file_path))
        module = loader.load_module()
    except FileNotFoundError as e:
        message = "Error: File '{}' not found.".format(file_path)
        raise CreprError(message, exit_code=1) from e
    except ImportError as e:
        message = "Error: Could not import '{}'.".format(file_path)
        raise CreprError(message, exit_code=1) from e
    except SyntaxError as e:
        message = "Error: Could not parse '{}'.".format(file_path)
        raise CreprError(message, exit_code=1) from e
    return module


def insert_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]:
    """Apply the changes to the source code of the given module."""
    src = inspect.getsource(module).splitlines()
    for lineno, change in sorted(changes.items(), reverse=True):
        for i, line in enumerate(change["lines"]):
            src.insert(lineno + i, line)
    return src


def remove_changes(module: ModuleType, changes: dict[int, Change]) -> list[str]:
    """Apply the changes to the source code of the given module."""
    src = inspect.getsource(module).splitlines()
    for lineno, change in sorted(changes.items(), reverse=True):
        for line in change["lines"]:
            assert src[lineno] == line  # noqa: S101
            del src[lineno]
    return src


def get_all_init_args(
    module: ModuleType,
) -> Iterator[tuple[type, MappingProxyType[str, inspect.Parameter], int, list[str]]]:
    """Get the __init__ arguments of all classes in a module."""
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
) -> dict[int, Change]:
    """Create a __repr__ method for each class of a python file."""
    changes: dict[int, Change] = {}
    for obj, init_args, lineno, source in get_all_init_args(module):
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


@app.command()
def add(
    files: Annotated[list[pathlib.Path], file_arg],
    kwarg_splat: Annotated[str, splat_option] = "{}",
    diff: Annotated[Optional[bool], diff_inline_option] = None,
) -> None:
    """Add __repr__ to all classes in the source code."""
    for module, file_path in get_modules(files):
        changes = create_repr(module, kwarg_splat)
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
    diff: Annotated[Optional[bool], diff_inline_option] = None,
) -> None:
    """Remove the __repr__ method from all classes in the source code."""
    for module, file_path in get_modules(files):
        changes = remove_repr(module)
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
        except CreprError as e:
            typer.secho(e.message, fg="red", err=True)


def process_file(file_path: pathlib.Path) -> None:
    """Process a single file and report classes without a __repr__ method."""
    module = load_module(file_path)
    if module is not None:
        classes = extract_classes(module)
        no_repr_classes = filter_no_repr(classes)
        report_results(file_path, classes, no_repr_classes)


def load_module(file_path: pathlib.Path) -> Optional[ModuleType]:
    """Load a module from a given file path."""
    try:
        return get_module(file_path)
    except CreprError as e:
        typer.secho(e.message, fg="red", err=True)
        return None


def extract_classes(module: ModuleType) -> List[Type]:
    """Extract classes from a module."""
    return [
        obj for _, obj in inspect.getmembers(module, inspect.isclass)
        if is_class_in_module(obj, module)
    ]


def filter_no_repr(classes: List[Type]) -> List[str]:
    """Filter out classes without a __repr__ method."""
    return [
        obj.__name__ for obj in classes
        if get_repr_source(obj)[1] == -1
    ]


def report_results(
    file_path: pathlib.Path,
    classes: List[Type],
    no_repr_classes: List[str]
) -> None:
    """Report the results of classes without a __repr__ method."""
    if no_repr_classes:
        typer.secho(
            "In module '{}': {} class(es) don't have a __repr__ method:".format(
                file_path, len(no_repr_classes)
            ),
            fg="yellow"
        )
        for class_name in no_repr_classes:
            typer.echo("{}: {}".format(file_path, class_name))
    else:
        typer.secho(
            "All {} class(es) in module '{}' have a __repr__ method.".format(
                len(classes), file_path
            ),
            fg="green"
        )

if __name__ == "__main__":
    app()
