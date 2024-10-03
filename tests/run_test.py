"""Tests for crepr module."""

import inspect
import pathlib
import tempfile
from types import ModuleType

import pytest
from typer.testing import CliRunner

from crepr import crepr

runner = CliRunner()


def test_get_init_source_no_init() -> None:
    """Test the edge-case when there is no __init__."""
    src, lineno = crepr.get_init_source(int)
    assert lineno == -1
    assert src == ""


def test_get_module() -> None:
    """Test get_module."""
    module = crepr.get_module("tests/classes/kw_only_test.py")

    assert isinstance(module, ModuleType)


def test_get_module_module_not_found() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(crepr.CreprError):
        crepr.get_module("tests/classes/file/not/found")


def test_get_module_import_error() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(crepr.CreprError):
        crepr.get_module("tests/classes/import_error.py")


def test_get_module_syntax_error() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(crepr.CreprError):
        crepr.get_module("tests/classes/c_test.c")


def test_get_init_args() -> None:
    """Test get_init_args."""
    module = crepr.get_module("tests/classes/kw_only_test.py")
    cls, init_args, lineno, src = next(crepr.get_all_init_args(module))
    assert cls.__name__ == "KwOnly"
    assert init_args is not None
    assert len(init_args) == 3
    assert init_args["self"].name == "self"
    assert init_args["name"].name == "name"
    assert init_args["name"].default is inspect._empty
    assert init_args["name"].annotation is str
    assert init_args["age"].name == "age"
    assert init_args["age"].default is inspect._empty
    assert init_args["age"].annotation is int
    assert lineno == 8
    assert src[0] == "    def __init__(self: Self, name: str, *, age: int) -> None:"


def test_get_init_args_no_init() -> None:
    """Test get_init_args."""
    module = crepr.get_module("tests/classes/class_no_init_test.py")
    assert not list(crepr.get_all_init_args(module))


def test_get_init_splat_kwargs() -> None:
    """Test get_init_args with a **kwargs splat."""
    module = crepr.get_module("tests/classes/splat_kwargs_test.py")
    cls, init_args, lineno, src = next(crepr.get_all_init_args(module))
    assert cls.__name__ == "SplatKwargs"
    assert init_args is not None
    assert len(init_args) == 3
    assert init_args["kwargs"].kind == inspect.Parameter.VAR_KEYWORD


def test_get_init_args_dataclass() -> None:
    """Test get_init_args with a dataclass."""
    module = crepr.get_module("tests/classes/dataclass_test.py")
    assert not list(crepr.get_all_init_args(module))


def test_get_repr_dataclass() -> None:
    """Test get_repr with a dataclass."""
    module = crepr.get_module("tests/classes/dataclass_test.py")

    for _, obj in inspect.getmembers(module, inspect.isclass):
        assert crepr.get_method_source(obj, "__repr__") == ("", -1)


def test_has_only_kwargs() -> None:
    """Test has_only_kwargs."""
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "name": inspect.Parameter("name", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "age": inspect.Parameter("age", inspect.Parameter.KEYWORD_ONLY),
        "kwargs": inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
    }

    assert crepr.has_only_kwargs(init_args)


def test_has_only_kwargs_false() -> None:
    """Test has_only_kwargs."""
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "name": inspect.Parameter("name", inspect.Parameter.VAR_POSITIONAL),
        "age": inspect.Parameter("age", inspect.Parameter.KEYWORD_ONLY),
    }

    assert not crepr.has_only_kwargs(init_args)


def test_has_only_kwargs_self_only() -> None:
    """Test has_only_kwargs."""
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
    }

    assert crepr.has_only_kwargs(init_args)


def test_create_repr_lines() -> None:
    """Test create_repr_lines."""
    param = inspect.Parameter("name", inspect.Parameter.POSITIONAL_OR_KEYWORD)
    class_name = "KwOnly"
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "name": param,
        "age": inspect.Parameter("age", inspect.Parameter.KEYWORD_ONLY),
    }

    lines = crepr.create_repr_lines(class_name, init_args, kwarg_splat="...")

    assert lines == [
        "",
        "    def __repr__(self) -> str:",
        '        """Create a string (c)representation for KwOnly."""',
        "        return (f'{self.__class__.__module__}.{self.__class__.__name__}('",
        "            f'name={self.name!r}, '",
        "            f'age={self.age!r}, '",
        "        ')')",
        "",
    ]


def test_create_repr_lines_splat_kwargs() -> None:
    """Test create_repr_lines."""
    class_name = "SplatKwargs"
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "kwargs": inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
    }

    lines = crepr.create_repr_lines(
        class_name,
        init_args,
        kwarg_splat="{}",
    )
    assert lines == [
        "",
        "    def __repr__(self) -> str:",
        '        """Create a string (c)representation for SplatKwargs."""',
        "        return (f'{self.__class__.__module__}.{self.__class__.__name__}('",
        "            f'**{},'",
        "        ')')",
        "",
    ]


def test_create_repr_lines_no_init() -> None:
    """Test create_repr_lines."""
    class_name = "NoInit"
    init_args = None

    lines = crepr.create_repr_lines(class_name, init_args, kwarg_splat="...")

    assert lines == []


def test_show() -> None:
    """Test the app happy path."""
    result = runner.invoke(crepr.app, ["add", "tests/classes/kw_only_test.py"])

    assert result.exit_code == 0
    assert "Create a string (c)representation for KwOnly" in result.stdout
    assert len(result.stdout.splitlines()) == 20


def test_show_no_init() -> None:
    """Test the app no reprs produced."""
    result = runner.invoke(crepr.app, ["add", "tests/classes/class_no_init_test.py"])

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 0


def test_show_no_classes() -> None:
    """Test the app no classes found."""
    file_name = "tests/classes/only_imported_test.py"
    result = runner.invoke(crepr.app, ["add", file_name])

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 0


def test_diff() -> None:
    """Print the diff."""
    result = runner.invoke(
        crepr.app,
        ["add", "--diff", "tests/classes/kw_only_test.py"],
    )

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 14
    assert result.stdout.startswith("---")
    assert result.stdout.splitlines()[1].startswith("+++")
    assert result.stdout.splitlines()[-1] == "+"


def test_write() -> None:
    """Write the changes."""
    file_name = pathlib.Path("tests/classes/kw_only_test.py")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with pathlib.Path.open(file_name, mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    result = runner.invoke(crepr.app, ["add", "--inline", str(temp_file_path)])
    assert result.exit_code == 0
    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        assert "    def __repr__(self) -> str:" in content
        assert '"""Create a string (c)representation for KwOnly."""' in content

    pathlib.Path.unlink(temp_file_path)


def test_remove() -> None:
    """Remove the __repr__."""
    file_name = pathlib.Path("tests/remove/splat_kwargs_test.py")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with pathlib.Path.open(file_name, mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    result = runner.invoke(crepr.app, ["remove", "--inline", str(temp_file_path)])
    assert result.exit_code == 0
    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        assert "__repr__" not in content

    pathlib.Path.unlink(temp_file_path)


def test_remove_diff() -> None:
    """Remove the changes."""
    file_name = "tests/remove/kw_only_test.py"

    result = runner.invoke(crepr.app, ["remove", "--diff", file_name])
    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 14
    assert result.stdout.startswith("---")
    assert result.stdout.splitlines()[1].startswith("+++")
    assert result.stdout.splitlines()[-1].startswith("-")


def test_show_remove() -> None:
    """Test the app happy path."""
    result = runner.invoke(crepr.app, ["remove", "tests/remove/kw_only_test.py"])

    assert result.exit_code == 0
    assert "__repr__" not in result.stdout
    assert len(result.stdout.splitlines()) == 13


def test_show_remove_no_repr() -> None:
    """Test the app happy path."""
    result = runner.invoke(crepr.app, ["remove", "tests/classes/class_no_init_test.py"])

    assert result.exit_code == 0
    assert "__repr__" not in result.stdout
    assert len(result.stdout.splitlines()) == 0


def test_report_missing() -> None:
    """Test report_missing command for classes without __repr__."""
    result = runner.invoke(
        crepr.app,
        ["report-missing", "tests/classes/class_without_repr.py"],
    )
    assert result.exit_code == 0
    assert "class_without_repr.py" in result.stdout
    assert "MyClassWithoutRepr" in result.stdout


def test_report_missing_error() -> None:
    """Test report_missing command when a file throws an import error."""
    file_path = "tests/classes/module_error.py"
    result = runner.invoke(crepr.app, ["report-missing", file_path])

    if result.exit_code != 0:
        raise (crepr.CreprError(result.output))


def test_report_missing_with_repr() -> None:
    """Test report_missing command for a class with a __repr__ method."""
    file_path = "tests/classes/class_with_repr_test.py"

    result = runner.invoke(crepr.app, ["report-missing", file_path])

    assert result.exit_code == 0, f"Unexpected exit code: {result.exit_code}"
    lines = result.stdout.splitlines()

    assert len(lines) == 0, "Expected 1 lines of output, but got many"


def test_add_ignore_existing_false() -> None:
    """Test add command when ignore_existing is False and __repr__ exists."""
    file_name = pathlib.Path("tests/classes/existing_repr_test.py")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with pathlib.Path.open(file_name, mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    result = runner.invoke(crepr.app, ["add", "--inline", str(temp_file_path)])
    assert result.exit_code == 0

    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        # Ensure a new __repr__ was added
        assert content.count("def __repr__") == 3
        # Ensure original __repr__ is still there
        assert "Existing repr magic method of the class" in content
        # Ensure new __repr__ was added
        assert "Create a string (c)representation for ExistingRepr" in content
    pathlib.Path.unlink(temp_file_path)


def test_add_ignore_existing_true() -> None:
    """Test add command when ignore_existing is True and __repr__ exists."""
    file_name = pathlib.Path("tests/classes/existing_repr_test.py")
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with pathlib.Path.open(file_name, mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    result = runner.invoke(
        crepr.app,
        ["add", "--ignore-existing", "--inline", str(temp_file_path)],
    )
    assert result.exit_code == 0

    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        # Ensure no new __repr__ was added
        assert content.count("def __repr__") == 2
        # Ensure original __repr__ is intact
        assert "Existing repr magic method of the class" in content
        # Ensure new __repr__ was not added
        assert "Create a string (c)representation for ExistingRepr" not in content

    pathlib.Path.unlink(temp_file_path)
