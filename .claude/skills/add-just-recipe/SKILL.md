---
name: add-just-recipe
description: Add, modify, or extend just recipes in this project. Use when asked to create new justfile recipes or modify existing ones.
allowed-tools: Read Edit Write Grep Glob Bash(just *)
---

Use this when asked to add, modify, or extend just recipes in this project.

## Steps

1. **Pick the child justfile.** Determine which `scripts/*.just` file owns the concern (lint, fmt, test, dev, setup, docs). If none fits, create a new `scripts/{concern}.just` starting with `set working-directory := '..'`.

2. **Add the implementation** in the child justfile. Keep recipe names short (e.g., `py`, `build`, `all`). Use `env("VAR", "default")` for any port/config that varies.

3. **Add the delegating recipe** in the root `justfile` under the matching section header. Follow the naming pattern `{concern}-{action}` and delegate with:
   ```just
   recipe-name *args:
       just -f scripts/{concern}.just {sub-recipe} {{args}}
   ```

4. **Update aggregates** if the new recipe should be included in `lint`, `test`, or `fmt`.

## Example: adding a Rust linter

`scripts/lint.just` -- append:
```just
rs *args:
    cargo clippy {{args}}
```

Root `justfile` -- add under `# -- Rust --` (new section):
```just
lint-rs *args:
    just -f scripts/lint.just rs {{args}}
```

Update aggregate:
```just
lint: lint-py lint-ts lint-md lint-rs
```
