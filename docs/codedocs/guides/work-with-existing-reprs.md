---
title: "Work With Existing Reprs And Kwargs"
description: "Handle classes that already define __repr__ and tune the placeholder used for dynamic keyword arguments."
---

This guide focuses on two behaviors that matter in real projects: classes that already have a `__repr__`, and constructors that include `**kwargs`.

## Problem

You need to run `crepr` across a mixed codebase where some classes already define `__repr__` manually and others accept open-ended keyword arguments.

## Solution

Use the default behavior to skip classes that already have a `__repr__`, and set `--ignore-existing` only when you explicitly want another generated method inserted anyway. For `**kwargs`, use `--kwarg-splat` to make the placeholder more meaningful for your team.

<Steps>
<Step>
### Start with the safe default

```bash
crepr add mixed_models.py --diff
```

By default, classes with an existing `__repr__` are skipped. The tests in `tests/classes/existing_repr_test.py` show that only classes without a current `__repr__` receive a generated one in this mode.

</Step>
<Step>
### Customize how `**kwargs` appears

```bash
crepr add mixed_models.py --kwarg-splat "kwargs=..."
```

This changes the generated placeholder fragment from the default `**{},` style to `**kwargs=...,`.

</Step>
<Step>
### Use `--ignore-existing` only deliberately

```bash
crepr add mixed_models.py --ignore-existing --diff
```

With that flag enabled, `add` will also generate a new `__repr__` for classes that already define one. It does not replace the old method; it inserts another one after the constructor.

</Step>
</Steps>

## Complete Runnable Example

```bash
cat > mixed_models.py <<'PY'
from typing import Self


class Existing:
    def __init__(self: Self, name: str) -> None:
        self.name = name

    def __repr__(self: Self) -> str:
        return f"Existing(name={self.name!r})"


class Flexible:
    def __init__(self: Self, name: str, **kwargs: str) -> None:
        self.name = name
        self.kwargs = kwargs
PY

crepr add mixed_models.py --diff
crepr add mixed_models.py --kwarg-splat "kwargs=..."
```

## What To Watch For

The flag name `--ignore-existing` can be read two ways. In `crepr`, it means “ignore the fact that a `__repr__` already exists and still add another one.” That behavior is implemented in `add` by calling `create_repr(module, kwarg_splat, not ignore_existing)`, which flips the guard passed into `create_repr`.

That is powerful but risky. Python keeps only the last method definition in the class body, so inserting a second `__repr__` effectively overrides the earlier one in the source order. Use the flag only when you truly want the generated method to replace the behavior of the earlier definition by virtue of being later in the class body.

## Real-World Pattern

For most teams, the right pattern is:

1. Run without `--ignore-existing`.
2. Review modules that were skipped because they already have a `__repr__`.
3. Hand-pick the few classes where you want automation to replace a manual implementation.

That keeps the tool helpful without turning it into a blunt overwrite mechanism.
