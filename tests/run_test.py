"""Tests for crepr module."""
import inspect

from typer.testing import CliRunner

from crepr import crepr

runner = CliRunner()


def test_get_class_objects() -> None:
    """Test get_class_objects."""
    class_objects = list(crepr.get_class_objects("tests.kw_only_test"))

    assert len(class_objects) == 1
    assert class_objects[0][0].__name__ == "KwOnly"
    assert class_objects[0][1].__name__ == "tests.kw_only_test"


def test_get_class_objects_module_not_found() -> None:
    """Exit gracefully if module not found."""
    class_objects = list(crepr.get_class_objects("tests.not_found"))

    assert not class_objects


def test_is_class_in_module() -> None:
    """Test is_class_in_module."""
    class_objects = list(crepr.get_class_objects("tests.kw_only_test"))
    assert crepr.is_class_in_module(class_objects[0][0], class_objects[0][1])


def test_get_init_args() -> None:
    """Test get_init_args."""
    class_objects = list(crepr.get_class_objects("tests.kw_only_test"))
    class_name, init_args = crepr.get_init_args(class_objects[0][0])
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


def test_get_init_args_no_init() -> None:
    """Test get_init_args."""
    class_objects = list(crepr.get_class_objects("tests.class_no_init_test"))
    class_name, init_args = crepr.get_init_args(class_objects[0][0])
    assert class_name == "NoInit"
    assert init_args is None


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
        "#  Class: KwOnly",
        "    def __repr__(self) -> str:",
        "        return (f'{self.__class__.__name__}('",
        "            f'name={self.name!r}, '",
        "            f'age={self.age!r}, '",
        "        ')')",
    ]


def test_create_repr_lines_no_init() -> None:
    """Test create_repr_lines."""
    class_name = "NoInit"
    init_args = None

    lines = crepr.create_repr_lines(class_name, init_args)

    assert lines == []


def test_app() -> None:
    """Test the app happy path."""
    result = runner.invoke(crepr.app, ["tests.kw_only_test"])

    assert result.exit_code == 0
    assert "#  Class: KwOnly" in result.stdout
    assert len(result.stdout.splitlines()) == 6


def test_app_no_init() -> None:
    """Test the app no reprs produced."""
    result = runner.invoke(crepr.app, ["tests.class_no_init_test"])

    assert result.exit_code == 1
    assert "#  Class: NoInit" not in result.stdout
    assert len(result.stdout.splitlines()) == 1


def test_app_no_classes() -> None:
    """Test the app no classes found."""
    result = runner.invoke(crepr.app, ["tests.only_imported_test"])

    assert result.exit_code == 1
    assert "No classes found in module 'tests.only_imported_test'." in result.stdout
    assert len(result.stdout.splitlines()) == 1
