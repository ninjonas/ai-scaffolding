set working-directory := '..'

# Pre-commit hook: lint, format, check conventions, and test if src/ changed
pre-commit:
    @echo "Running pre-commit checks..."
    just lint
    just fmt
    just check
    bash -c 'if git diff --cached --name-only | grep -q "^src/"; then echo "src/ changes detected — running tests..."; just test; else echo "No src/ changes — skipping tests."; fi'
    @echo "Pre-commit checks passed."

# Pre-push hook: run tests
pre-push:
    @echo "Running pre-push checks..."
    just test
    @echo "Pre-push checks passed."
