---
title: "Review Diffs And Apply Changes"
description: "Generate unified diffs with crepr and then switch to inline writes once the proposed edits look correct."
---

This guide covers the practical two-step workflow for teams that want reviewable output first and file mutation second. It is the safest path when `crepr` is introduced into a shared repository or wired into a pre-commit process.

## Problem

You want generated `__repr__` methods, but you do not want a code-modifying CLI to rewrite source files before you have seen exactly what will change.

## Solution

Use `--diff` to generate a unified diff, review the patch, and then rerun the same command with `--inline` once the output is acceptable.

<Steps>
<Step>
### Generate a diff

```bash
crepr add account.py --diff
```

The diff is produced by `print_diff`, which wraps `difflib.unified_diff`.

</Step>
<Step>
### Inspect the patch

Look for the new `__repr__` block inserted after the constructor:

```diff
@@
 class Account:
     def __init__(self, username: str, *, active: bool) -> None:
         self.username = username
         self.active = active
+
+    def __repr__(self) -> str:
+        """Create a string (c)representation for Account."""
+        return (f'{self.__class__.__module__}.{self.__class__.__name__}('
+            f'username={self.username!r}, '
+            f'active={self.active!r}, '
+        ')')
```

</Step>
<Step>
### Apply the same change inline

```bash
crepr add account.py --inline
```

At this point the file is rewritten with the generated method inserted in place.

</Step>
</Steps>

## Complete Runnable Example

```bash
cat > account.py <<'PY'
from typing import Self


class Account:
    def __init__(self: Self, username: str, *, active: bool) -> None:
        self.username = username
        self.active = active
PY

crepr add account.py --diff
crepr add account.py --inline
```

After the second command, `account.py` contains the new `__repr__`.

## Why This Pattern Works Well

Diff mode and inline mode share the same selection and generation pipeline. There is no “preview implementation” and “apply implementation” that could diverge. The only difference is whether `apply_changes` calls `print_diff` or writes the resulting source back through `file_path.open(mode="w" encoding="UTF-8")`.

That makes this workflow predictable in real repositories. If the diff looks correct, the inline output should match it exactly. For teams using code review or commit hooks, the diff-first pattern keeps `crepr` transparent and easy to trust.

## Variations

If you want to inspect several files in one run, pass them all to `crepr add ... --diff`. Broken modules are skipped individually, so one import failure does not cancel diff generation for the rest of the batch.
