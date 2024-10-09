#!/usr/bin/env python3
"""Check if the version in the about.py file matches the given version.

Usage: check_version_tag.py <filename> <tag_version>

This script checks if the version in the project metadata matches the given version.

"""
import argparse
import re
import sys
from pathlib import Path

pattern = (
    r"^(?P<version>\d+\.\d+)(?P<extraversion>(?:\.\d+)*)"
    r"(?:(?P<prerel>[abc]|rc)\d+(?:\.\d+)?)?(?P<postdev>(\.post(?P<post>\d+))?"
    r"(\.dev(?P<dev>\d+))?)?$"
)


def guess_file_name() -> Path:
    """Guesses the file name of the PKG-INFO file within an .egg-info directory.

    This function searches for directories with the .egg-info extension in the current
    directory. If such a directory is found, it returns the path to the PKG-INFO file
    within that directory.
    If no .egg-info directory is found, it writes an error message to stdout and
    exits the program with a status code of 1.

    Returns:
        Path: The path to the PKG-INFO file within the found .egg-info directory.

    Raises:
        SystemExit: If no .egg-info directory is found.

    """
    """"""
    egg_info_dirs = list(Path().glob("*.egg-info"))
    if egg_info_dirs:
        return egg_info_dirs[0] / "PKG-INFO"
    sys.stdout.write("No filename provided and no '*.egg-info' directory found\n")
    sys.exit(1)


def get_version_from_pkg_info(file_name: str) -> str:
    """Get the version from the file."""
    file_path = Path(file_name)
    if not file_name:
        file_path = guess_file_name()
    try:
        with file_path.open("r") as f:
            for line in f:
                if line.startswith("Version:"):
                    return line.split(":")[1].strip()
                if line.startswith("__version__"):
                    return line.split("=")[1].strip()
    except Exception as e:  # noqa: BLE001
        sys.stdout.write(f"Error loading file {file_name}: {e}\n")
        sys.exit(1)
    sys.stdout.write(f"No Version found in '{file_name}'\n")
    sys.exit(1)


def main(file_name: str, tag_name: str) -> None:
    """Check if the version in the filename file matches the given version."""
    version = get_version_from_pkg_info(file_name)
    errors = False
    if version != tag_name:
        sys.stdout.write(f"Version {version} does not match tag {tag_name}\n")
        errors = True
    if not re.match(pattern, tag_name):
        sys.stdout.write(f"Tag name '{tag_name}' is not PEP-386 compliant\n")
        errors = True
    if not re.match(pattern, version):
        sys.stdout.write(f"Version {version} is not PEP-386 compliant\n")
        errors = True
    if errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Check if the version in the metadata matches the given version.",
    )
    parser.add_argument("tag_version", help="The version tag to compare against.")
    parser.add_argument(
        "filename",
        nargs="?",
        default="",
        help="The path to the file containing the version information.",
    )

    args = parser.parse_args()

    main(args.filename, args.tag_version)
