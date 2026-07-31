---
title: "Generate And Preview Reprs"
description: "Use crepr in preview mode to inspect generated __repr__ methods before touching source files."
---

This guide covers the lowest-risk way to adopt `crepr`: generate candidate `__repr__` methods, inspect the output, and decide whether the file is a good fit before applying any edits.

## When To Use This Guide

Use preview mode when you are introducing `__repr__` coverage to an existing module, when you are unsure whether constructor shapes are supported, or when you want to confirm how `**kwargs` placeholders will look before changing code.

<Steps>
<Step>

### Create or choose a supported module

Use a class with an explicit `__init__` and named parameters:

```python
from typing import Self


class Account:
    def __init__(self: Self, username: str, *, active: bool) -> None:
        self.username = username
        self.active = active
```

</Step>
<Step>

### Run `crepr add` without flags

```bash
crepr add account.py
```

Without `--diff` or `--inline`, the command stays in preview mode and prints only the generated method body.

</Step>
<Step>

### Read the generated method carefully

Expected output:

```text
__repr__ generated for class: Account

    def __repr__(self) -> str:
        """Create a string (c)representation for Account."""
        return (f'{self.__class__.__module__}.{self.__class__.__name__}('
            f'username={self.username!r}, '
            f'active={self.active!r}, '
        ')')
```

If the output looks right, move on to the diff or inline workflows described in the next guides.

</Step>
</Steps>

## What To Verify In The Output

- The class appears in the output at all. If it does not, the constructor is probably unsupported or not declared directly on the class.
- The parameter order matches your constructor order.
- Keyword-only fields appear with the names you expect.
- The fully qualified class name in the return value is acceptable for your logging or debugging style.

## Complete Runnable Example

```bash
cat > sample.py <<'PY'
from typing import Self


class Account:
    def __init__(self: Self, username: str, *, active: bool) -> None:
        self.username = username
        self.active = active
PY

crepr add sample.py
```

The output should show a generated `__repr__` but should not modify `sample.py`.

## Real-World Pattern

Preview mode is especially useful when adding debug-friendly representations across several application modules. Because `get_modules` processes each file independently, you can pass multiple file paths in one command and still get output only for the classes that qualify. Files that fail to import are skipped with an error message instead of aborting the entire batch.

That behavior makes preview mode a good audit step before mass adoption. You can quickly identify unsupported modules, imported-only facades, and classes with `*args` constructors without creating noisy diffs or partially edited files.
