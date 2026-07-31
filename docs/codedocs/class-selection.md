---
title: "Class Selection"
description: "See how crepr decides which classes are eligible for generated or removable __repr__ methods."
---

Class selection is the gatekeeper stage in `crepr`. After loading a module, the tool does not blindly modify every class it can see. Instead, it filters down to classes defined in the target file and then checks whether their constructor shape can be expressed in the generated `__repr__`.

## What This Concept Is

The central function is `get_all_init_args(module: ModuleType) -> Iterator[tuple[type, MappingProxyType[str, inspect.Parameter], int, list[str]]]` in `crepr/crepr.py`. It yields only classes that meet three conditions:

1. The class is defined in the loaded module, not imported from somewhere else.
2. The class declares its own `__init__` in `cls.__dict__`.
3. The constructor parameters are limited to `POSITIONAL_OR_KEYWORD`, `KEYWORD_ONLY`, and `VAR_KEYWORD`.

This concept exists to keep generation deterministic. If the constructor includes `*args`, inherited initialization, or an auto-generated dataclass initializer, `crepr` does not try to infer fields heuristically.

## How It Relates To Other Concepts

Selection sits between [Discovery And Loading](/docs/discovery-and-loading) and [Repr Generation](/docs/repr-generation). If discovery answers “can this file be inspected?”, selection answers “which classes are safe enough to describe from `__init__`?”.

## Internal Walkthrough

The first filter is `is_class_in_module(cls: type, module: ModuleType) -> bool`. It compares `cls.__module__` with `module.__name__`, which excludes re-exported imports such as the symbols in `tests/classes/only_imported_test.py`.

The second filter is `get_init_args(cls: type)`. It returns constructor parameters only when `__init__` exists directly on the class. That means a class like `NoInit` from `tests/classes/class_no_init_test.py` is skipped even though Python can instantiate it, because there is no explicit constructor to inspect. Dataclasses are skipped for the same reason: their generated initializer is not present in `cls.__dict__`.

The third filter is `has_only_kwargs(init_args)`. Despite the name, it allows normal positional-or-keyword parameters, keyword-only parameters, and `**kwargs`. What it rejects is `VAR_POSITIONAL`, which is how Python represents `*args`. The test fixture `tests/classes/class_pos_args_test.py` demonstrates that `*args` makes a class ineligible.

```mermaid
flowchart TD
  A[inspect.getmembers(module, inspect.isclass)] --> B{Defined in module?}
  B -->|No| X[Skip]
  B -->|Yes| C{Explicit __init__ in cls.__dict__?}
  C -->|No| X
  C -->|Yes| D{Supported parameter kinds only?}
  D -->|No| X
  D -->|Yes| E[Yield class, parameters, line number, source]
```

## Basic Usage Example

This file is eligible because it has an explicit constructor with a normal parameter and a keyword-only field:

```python
from typing import Self


class User:
    def __init__(self: Self, username: str, *, admin: bool) -> None:
        self.username = username
        self.admin = admin
```

Running `crepr add user.py` will generate a `__repr__` for `User`.

## Advanced Example

This file mixes supported and unsupported shapes:

```python
from dataclasses import dataclass
from typing import Self


class Good:
    def __init__(self: Self, name: str, **kwargs: str) -> None:
        self.name = name
        self.kwargs = kwargs


class SkipVarArgs:
    def __init__(self: Self, x: int, *args: int) -> None:
        self.x = x


@dataclass
class SkipDataclass:
    x: int
```

`crepr add mixed.py` will consider `Good`, skip `SkipVarArgs` because of `*args`, and skip `SkipDataclass` because there is no explicit `__init__` in the class body for `get_init_args` to inspect.

<Callout type="warn">A generated `__repr__` only reflects constructor parameters, not every attribute assigned later in the class. If your object mutates significantly after `__init__`, the resulting representation may be incomplete even when the class is technically eligible.</Callout>

<Accordions>
<Accordion title="Why does crepr skip dataclasses and inherited constructors?">
This is a deliberate consequence of using `cls.__dict__` as the source of truth. By requiring an explicit class-local `__init__`, `crepr` avoids guessing which inherited or synthesized fields belong in the generated representation. That keeps line-number insertion straightforward, because the tool knows exactly where the constructor source ends. The downside is that some ergonomic Python patterns, especially dataclasses and inheritance-heavy models, are outside the supported set even though they could theoretically produce a useful `__repr__`.
</Accordion>
<Accordion title="Why reject *args but allow **kwargs?">
`create_repr_lines` can express named fields because each parameter has a stable label like `name` or `age`. A `*args` parameter does not give the tool meaningful names, so the output would either be generic and low-value or require assumptions about positional semantics. `**kwargs` is different because the generated method can emit a placeholder string such as `**{},` or a custom token passed through `--kwarg-splat`. That preserves the existence of extra keyword data without pretending the tool knows every dynamic key.
</Accordion>
</Accordions>

Once a class passes selection, `crepr` can build the exact `__repr__` lines to insert or compare.
