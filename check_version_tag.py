# usr/bin/env python3
"""Check if the version in the about.py file matches the given version.

Usage: check_version_tag.py <filename> <tag_version>

This script is used to check if the version in the about.py file matches the
given version. The version in the about.py file is expected to be a string
assigned to the __version__ attribute of the module. The given version is
expected to be a PEP-386 compliant version string.
"""
import importlib.util
import re
import sys
from typing import cast

pattern = (
    r"^(?P<version>\d+\.\d+)(?P<extraversion>(?:\.\d+)*)"
    r"(?:(?P<prerel>[abc]|rc)\d+(?:\.\d+)?)?(?P<postdev>(\.post(?P<post>\d+))?"
    r"(\.dev(?P<dev>\d+))?)?$"
)


def get_version_from_module(file_name: str) -> str:
    """Get the version from the module."""
    try:
        spec = importlib.util.spec_from_file_location("module.name", file_name)
        assert spec is not None  # noqa: S101
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None  # noqa: S101
        spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001
        sys.stdout.write(f"Error loading file {file_name}: {e}")
        sys.exit(1)
    try:
        version = module.__version__
        if not isinstance(version, str):
            sys.stdout.write(f"Version in {file_name} is not a string")
            sys.exit(1)
        return cast(str, module.__version__)
    except AttributeError:
        sys.stdout.write(f"Module {file_name} has no __version__ attribute")
        sys.exit(1)


def main(filename: str, tag_name: str) -> None:
    """Check if the version in the filename file matches the given version."""
    version = get_version_from_module(filename)
    errors = False
    if version != tag_name:
        sys.stdout.write(f"Version {version} does not match tag {tag_name}")
        errors = True
    if not re.match(pattern, tag_name):
        sys.stdout.write(f"Tag name '{tag_name}' is not PEP-386 compliant")
        errors = True
    if not re.match(pattern, version):
        sys.stdout.write(f"Version {version} is not PEP-386 compliant")
        errors = True
    if errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    try:
        file_name = sys.argv[1]
        tag_name = sys.argv[2]
    except IndexError:
        sys.stdout.write("Usage: check_version_tag.py <filename> <tag_version>")
        sys.exit(1)
    main(file_name, tag_name)
