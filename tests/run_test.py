"""Tests for crepr module."""

import inspect
import pathlib
import tempfile
from types import ModuleType
from typing import Final

import pytest
from typer.testing import CliRunner

from crepr import crepr

runner = CliRunner()

test_dir: Final = pathlib.Path(__file__).parent


def test_get_init_source_no_init() -> None:
    """Test the edge-case when there is no __init__."""
    src, lineno = crepr.get_init_source(int)
    assert lineno == -1
    assert src == ""


def test_get_module() -> None:
    """Test get_module."""
    path = test_dir / "classes" / "kw_only_test.py"
    module = crepr.get_module(path)

    assert isinstance(module, ModuleType)


def test_get_module_module_not_found() -> None:
    """Exit gracefully if module not found."""
    path = test_dir / "classes" / "file" / "not" / "found"
    with pytest.raises(crepr.CreprError):
        crepr.get_module(path)


def test_get_module_import_error() -> None:
    """Exit gracefully if module not found."""
    path = test_dir / "classes" / "import_error.py"
    with pytest.raises(crepr.CreprError):
        crepr.get_module(path)


def test_get_module_syntax_error() -> None:
    """Exit gracefully if module not found."""
    path = test_dir / "classes" / "c_test.c"
    with pytest.raises(crepr.CreprError):
        crepr.get_module(path)


def test_get_init_args() -> None:
    """Test get_init_args."""
    path = test_dir / "classes" / "kw_only_test.py"
    module = crepr.get_module(path)
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
    path = test_dir / "classes" / "class_no_init_test.py"
    module = crepr.get_module(path)
    assert not list(crepr.get_all_init_args(module))


def test_get_init_splat_kwargs() -> None:
    """Test get_init_args with a **kwargs splat."""
    path = test_dir / "remove" / "splat_kwargs_test.py"
    module = crepr.get_module(path)
    cls, init_args, lineno, src = next(crepr.get_all_init_args(module))
    assert cls.__name__ == "SplatKwargs"
    assert init_args is not None
    assert len(init_args) == 3
    assert init_args["kwargs"].kind == inspect.Parameter.VAR_KEYWORD


def test_get_init_args_dataclass() -> None:
    """Test get_init_args with a dataclass."""
    path = test_dir / "classes" / "dataclass_test.py"
    module = crepr.get_module(path)
    assert not list(crepr.get_all_init_args(module))


def test_get_repr_dataclass() -> None:
    """Test get_repr with a dataclass."""
    path = test_dir / "classes" / "dataclass_test.py"
    module = crepr.get_module(path)

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


def test_get_modules() -> None:
    """Test get_modules."""
    paths = [
        test_dir / "classes" / "kw_only_test.py",
        test_dir / "remove" / "splat_kwargs_test.py",
        test_dir / "classes" / "dataclass_test.py",
        test_dir / "classes" / "class_no_init_test.py",
        test_dir / "classes" / "import_error.py",
        test_dir / "classes" / "c_test.c",
        test_dir / "classes" / "file" / "not" / "found",
        test_dir / "classes",
    ]
    mod_path = list(crepr.get_modules(paths))
    assert len(mod_path) == 4
    assert all(isinstance(mp[0], ModuleType) for mp in mod_path)


def test_show() -> None:
    """Test the app happy path."""
    path = test_dir / "classes" / "kw_only_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["add", filename])

    assert result.exit_code == 0
    assert "__repr__ generated for class: KwOnly" in result.stdout
    assert "Create a string (c)representation for KwOnly" in result.stdout
    assert len(result.stdout.splitlines()) == 10


def test_show_no_init() -> None:
    """Test the app no reprs produced."""
    path = test_dir / "classes" / "class_no_init_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["add", filename])

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 0


def test_show_no_classes() -> None:
    """Test the app no classes found."""
    path = test_dir / "classes" / "only_imported_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["add", filename])

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 0


def test_diff() -> None:
    """Print the diff."""
    path = test_dir / "classes" / "kw_only_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["add", "--diff", filename])

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 14
    assert result.stdout.startswith("---")
    assert result.stdout.splitlines()[1].startswith("+++")
    assert result.stdout.splitlines()[-1] == "+"


def test_write() -> None:
    """Write the changes."""
    path = test_dir / "classes" / "kw_only_test.py"

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with path.open(mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    temp_file_name = str(temp_file_path.absolute())
    result = runner.invoke(crepr.app, ["add", "--inline", temp_file_name])
    assert result.exit_code == 0
    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        assert "    def __repr__(self) -> str:" in content
        assert '"""Create a string (c)representation for KwOnly."""' in content

    pathlib.Path.unlink(temp_file_path)


def test_remove() -> None:
    """Remove the __repr__."""
    path = test_dir / "remove" / "splat_kwargs_test.py"

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with pathlib.Path.open(path, mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    tmp_file_name = str(temp_file_path.absolute())
    result = runner.invoke(crepr.app, ["remove", "--inline", tmp_file_name])
    assert result.exit_code == 0
    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        assert "__repr__" not in content

    pathlib.Path.unlink(temp_file_path)


def test_remove_diff() -> None:
    """Remove the changes."""
    path = test_dir / "remove" / "kw_only_test.py"
    file_name = str(path.absolute())

    result = runner.invoke(crepr.app, ["remove", "--diff", file_name])
    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 14
    assert result.stdout.startswith("---")
    assert result.stdout.splitlines()[1].startswith("+++")
    assert result.stdout.splitlines()[-1].startswith("-")


def test_show_remove() -> None:
    """Test the app happy path."""
    path = test_dir / "remove" / "kw_only_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["remove", filename])

    assert result.exit_code == 0
    assert "__repr__ removed for class: KwOnly" in result.stdout
    assert len(result.stdout.splitlines()) == 10


def test_show_remove_no_repr() -> None:
    """Test the app happy path."""
    path = test_dir / "classes" / "class_no_init_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["remove", filename])

    assert result.exit_code == 0
    assert "__repr__" not in result.stdout
    assert len(result.stdout.splitlines()) == 0


def test_add_ignore_existing_false() -> None:
    """Test add command when ignore_existing is False and __repr__ exists."""
    path = test_dir / "classes" / "existing_repr_test.py"
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with path.open(mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    tmp_file_name = str(temp_file_path.absolute())
    result = runner.invoke(crepr.app, ["add", "--inline", tmp_file_name])
    assert result.exit_code == 0

    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        # Ensure a new __repr__ was added
        assert content.count("def __repr__") == 2
        # Ensure original __repr__ is still there
        assert "Existing repr magic method of the class" in content
        # Ensure new __repr__ was added
        assert "Create a string (c)representation for ExistingRepr" not in content
    pathlib.Path.unlink(temp_file_path)


def test_add_ignore_existing_true() -> None:
    """Test add command when ignore_existing is True and __repr__ exists."""
    path = test_dir / "classes" / "existing_repr_test.py"
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        with path.open(mode="rt", encoding="UTF-8") as f:
            temp_file.write(f.read())
        temp_file_path = pathlib.Path(temp_file.name)

    tmp_file_name = str(temp_file_path.absolute())
    result = runner.invoke(
        crepr.app,
        ["add", "--ignore-existing", "--inline", tmp_file_name],
    )
    assert result.exit_code == 0

    with pathlib.Path.open(temp_file_path, mode="rt", encoding="UTF-8") as f:
        content = f.read()
        # Ensure no new __repr__ was added
        assert content.count("def __repr__") == 3
        # Ensure original __repr__ is intact
        assert "Existing repr magic method of the class" in content
        # Ensure new __repr__ was not added
        assert "Create a string (c)representation for ExistingRepr" in content

    pathlib.Path.unlink(temp_file_path)


def test_add_show_only_changes() -> None:
    """Test that only proposed changes are shown without --diff or --inline."""
    path = test_dir / "classes" / "kw_only_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["add", filename])

    assert result.exit_code == 0
    assert "__repr__ generated for class: KwOnly" in result.stdout
    assert "def __repr__(self) -> str:" in result.stdout
    assert (
        "return (f'{self.__class__.__module__}.{self.__class__.__name__}("
        in result.stdout
    )
    assert "f'name={self.name!r}, '" in result.stdout
    assert "f'age={self.age!r}, '" in result.stdout
    assert "')')" in result.stdout


def test_remove_show_only_changes() -> None:
    """Test that only proposed removals are shown without --diff or --inline."""
    path = test_dir / "remove" / "kw_only_test.py"
    filename = str(path.absolute())
    result = runner.invoke(crepr.app, ["remove", filename])

    assert result.exit_code == 0
    assert "__repr__ removed for class: KwOnly" in result.stdout
    assert "def __repr__(self: Self) -> str:" in result.stdout
    assert '"""Create a string (c)representation for KwOnly."""' in result.stdout
    assert "return (" in result.stdout
    assert 'f"{self.__class__.__module__}.{self.__class__.__name__}("' in result.stdout
    assert 'f"name={self.name!r}, "' in result.stdout
    assert 'f"age={self.age!r}, "' in result.stdout
    assert '")"\n' in result.stdout
    assert ")" in result.stdout
