---
title: "Remove Generated Reprs"
description: "Use crepr remove to preview, diff, or delete __repr__ methods from supported classes."
---

This guide shows how to back out `__repr__` methods with the same workflow used for generation. The `remove` command matters when a module changes shape, when you want to undo a previous automation pass, or when you want to hand-write a more specific representation.

## Problem

You already have `__repr__` methods in a file and want a repeatable way to remove them without manually editing each class.

## Solution

Use `crepr remove` with the same three execution styles as `add`: preview, diff, and inline.

<Steps>
<Step>
### Preview what will be removed

```bash
crepr remove models.py
```

This prints the exact `__repr__` block targeted for each eligible class.

</Step>
<Step>
### Review the deletion as a diff

```bash
crepr remove models.py --diff
```

The removed lines appear with `-` prefixes in the unified diff.

</Step>
<Step>
### Apply the deletion

```bash
crepr remove models.py --inline
```

Inline mode rewrites the file with the matched `__repr__` lines removed.

</Step>
</Steps>

## Complete Runnable Example

```bash
cat > models.py <<'PY'
from typing import Self


class Account:
    def __init__(self: Self, username: str, *, active: bool) -> None:
        self.username = username
        self.active = active

    def __repr__(self: Self) -> str:
        """Create a string (c)representation for Account."""
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}("
            f"username={self.username!r}, "
            f"active={self.active!r}, "
            ")"
        )
PY

crepr remove models.py --diff
crepr remove models.py --inline
```

## How Removal Works Internally

`remove_repr(module)` does not search textually for the string `def __repr__`. It asks `get_repr_source` for the actual method source attached to each selected class, splits that source into lines, and returns a change map keyed by the method’s starting line number. `remove_changes` then deletes those exact lines from the module source in reverse order.

This is more precise than a text search, but it also means removal depends on the same class-selection rules as generation. A class without an explicit supported constructor is not part of the removal pipeline, even if it contains a `__repr__`.

## Real-World Pattern

Use `remove` when refactoring older modules before re-running `add` with a different `--kwarg-splat` convention or before replacing generated output with a hand-written representation. The preview and diff modes let you confirm the tool is targeting the expected methods before any destructive write occurs.
