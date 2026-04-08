## Git commit messages

Use semantic commit messages in this format:

```
<type>(<scope>): <subject>
```

### Types

- `feat` — new feature or capability
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `docs` — documentation only
- `style` — formatting, linting fixes (no logic change)
- `test` — adding or updating tests
- `chore` — build scripts, deps, config, CI
- `perf` — performance improvement

### Scope

Optional, refers to the area of the codebase: `api`, `web`, `scripts`, `docs`, `config`.

### Rules

- Subject line: imperative mood, lowercase, no period, under 72 chars
- Body (optional): explain **why**, not what — the diff shows what changed
- One logical change per commit — don't mix unrelated changes

### Examples

```
feat(api): add user registration endpoint
fix(web): prevent double-submit on login form
chore(scripts): add docs-build recipe
refactor(api): extract auth middleware from main
docs: update setup guide with port configuration
```
