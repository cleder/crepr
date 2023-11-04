"""Tests for crepr module."""
import inspect

import click
import pytest
from typer.testing import CliRunner

from crepr import crepr

runner = CliRunner()


def test_get_init_source_no_init() -> None:
    """Test the edge-case when there is no __init__."""
    src, lineno = crepr.get_init_source(int)
    assert lineno == -1
    assert src == ""


def test_get_class_objects() -> None:
    """Test get_class_objects."""
    class_objects = list(crepr.get_class_objects("tests/kw_only_test.py"))

    assert len(class_objects) == 1
    assert class_objects[0][0].__name__ == "KwOnly"


def test_get_class_objects_module_not_found() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(click.exceptions.Exit):
        list(crepr.get_class_objects("tests/file/not/found"))


def test_get_class_objects_import_error() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(click.exceptions.Exit):
        list(crepr.get_class_objects("tests/import_error.py"))


def test_get_class_objects_syntax_error() -> None:
    """Exit gracefully if module not found."""
    with pytest.raises(click.exceptions.Exit):
        list(crepr.get_class_objects("tests/c_test.c"))


def test_is_class_in_module() -> None:
    """Test is_class_in_module."""
    class_objects = list(crepr.get_class_objects("tests/kw_only_test.py"))
    assert crepr.is_class_in_module(class_objects[0][0], class_objects[0][1])


def test_get_init_args() -> None:
    """Test get_init_args."""
    class_objects = list(crepr.get_class_objects("tests/kw_only_test.py"))
    class_name, init_args, lineno, src = crepr.get_init_args(class_objects[0][0])
    assert class_name == "KwOnly"
    assert init_args is not None
    assert len(init_args) == 3
    assert init_args["self"].name == "self"
    assert init_args["name"].name == "name"
    assert init_args["name"].default is inspect._empty
    assert init_args["name"].annotation == str
    assert init_args["age"].name == "age"
    assert init_args["age"].default is inspect._empty
    assert init_args["age"].annotation == int
    assert lineno == 6
    assert src.startswith("    def __init__(self, name: str, *, age: int) -> None:")


def test_get_init_args_no_init() -> None:
    """Test get_init_args."""
    class_objects = list(crepr.get_class_objects("tests/class_no_init_test.py"))
    class_name, init_args, lineno, src = crepr.get_init_args(class_objects[0][0])
    assert class_name == "NoInit"
    assert init_args is None
    assert lineno == -1
    assert src is None


def test_has_only_kwargs() -> None:
    """Test has_only_kwargs."""
    init_args = {
        "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "name": inspect.Parameter("name", inspect.Parameter.POSITIONAL_OR_KEYWORD),
        "age": inspect.Parameter("age", inspect.Parameter.KEYWORD_ONLY),
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

    lines = crepr.create_repr_lines(class_name, init_args)

    assert lines == [
        "",
        "    def __repr__(self) -> str:",
        '        """Create a string (c)representation of the class."""',
        "        return (f'{self.__class__.__name__}('",
        "            f'name={self.name!r}, '",
        "            f'age={self.age!r}, '",
        "        ')')",
        "",
    ]


def test_create_repr_lines_no_init() -> None:
    """Test create_repr_lines."""
    class_name = "NoInit"
    init_args = None

    lines = crepr.create_repr_lines(class_name, init_args)

    assert lines == []


def test_app() -> None:
    """Test the app happy path."""
    result = runner.invoke(crepr.app, ["tests/kw_only_test.py"])

    assert result.exit_code == 0
    assert "Create a string (c)representation of the class" in result.stdout
    assert len(result.stdout.splitlines()) == 18


def test_app_no_init() -> None:
    """Test the app no reprs produced."""
    result = runner.invoke(crepr.app, ["tests/class_no_init_test.py"])

    assert result.exit_code == 1
    assert "#  Class: NoInit" not in result.stdout
    assert len(result.stdout.splitlines()) == 1


def test_app_no_classes() -> None:
    """Test the app no classes found."""
    file_name = "tests/only_imported_test.py"
    result = runner.invoke(crepr.app, [file_name])

    assert result.exit_code == 1
    assert f"Error: No __repr__ could be generated for '{file_name}'." in result.stdout
    assert len(result.stdout.splitlines()) == 1
