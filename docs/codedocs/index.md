---
title: "Getting Started"
description: "Learn what crepr does, why it exists, and how to generate __repr__ methods for Python classes."
---

`crepr` is a typed Python CLI that inspects a module, discovers eligible classes, and generates or removes `__repr__` methods based on the class `__init__` signature.

## The Problem

- Hand-written `__repr__` methods are repetitive and easy to let drift away from the actual constructor fields.
- Reviewers often want readable object representations for debugging, but adding them across a module is low-value manual work.
- Existing models may mix positional, keyword-only, and `**kwargs` parameters, which makes consistent formatting tedious to maintain.
- Bulk cleanup is annoying when you want to preview generated methods first, compare the diff, or remove previously generated `__repr__` blocks.

## The Solution

`crepr` loads a Python source file as a module, walks the classes defined in that file, filters down to classes it can safely describe, and then emits source lines for a `__repr__` method. By default it prints the generated method without touching the file. You can switch to `--diff` for a unified diff or `--inline` to write the result back to disk.

```bash
crepr add tests/classes/kw_only_test.py
```

```python
def __repr__(self) -> str:
    """Create a string (c)representation for KwOnly."""
    return (f'{self.__class__.__module__}.{self.__class__.__name__}('
        f'name={self.name!r}, '
        f'age={self.age!r}, '
    ')')
```

## Installation

<Callout type="info">`crepr` is published as a Python package, so installation uses Python package managers rather than npm.</Callout>

" "poetry"]}>
<Tab value="pip">

```bash
pip install crepr
```

</Tab>
<Tab value="uv">

```bash
uv tool install crepr
```

</Tab>
<Tab value="pipx">

```bash
pipx install crepr
```

</Tab>
<Tab value="poetry">

```bash
poetry add --group dev crepr
```

</Tab>
</Tabs>

## Quick Start

Create a file named `person.py`:

```python
from typing import Self


class Person:
    def __init__(self: Self, name: str, *, age: int) -> None:
        self.name = name
        self.age = age
```

Run `crepr` in preview mode:

```bash
crepr add person.py
```

Expected output:

```text
__repr__ generated for class: Person

    def __repr__(self) -> str:
        """Create a string (c)representation for Person."""
        return (f'{self.__class__.__module__}.{self.__class__.__name__}('
            f'name={self.name!r}, '
            f'age={self.age!r}, '
        ')')
```

If you rerun the command with `--inline`, `crepr` writes the generated block into `person.py`. If you prefer a patch-like review step, use `--diff` instead and inspect the unified diff before changing the source file.

## Key Features

- Python 3.12+ CLI built with `typer-slim`
- Generates `__repr__` from explicit `__init__` parameters
- Supports keyword-only parameters and configurable `**kwargs` placeholders
- Can print proposed methods, show unified diffs, or edit files inline
- Can remove existing `__repr__` implementations using the same module-discovery pipeline
- Ignores imported classes and classes without a compatible explicit `__init__`

## Next Pages

<Cards>
  <Card title="Architecture" href="/docs/architecture">See how the CLI loads modules, selects classes, and writes source changes.</Card>
  <Card title="Core Concepts" href="/docs/discovery-and-loading">Understand the loading, filtering, generation, and edit-mode concepts that shape crepr.</Card>
  <Card title="API Reference" href="/docs/api-reference/package-exports">Inspect every public function, class, module export, and CLI command.</Card>
</Cards>
