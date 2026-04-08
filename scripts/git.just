set working-directory := '..'

# Pre-commit hook: lint, format, and check conventions
pre-commit:
    @echo "Running pre-commit checks..."
    just lint
    just fmt
    just check
    @echo "Pre-commit checks passed."

# Pre-push hook: run tests
pre-push:
    @echo "Running pre-push checks..."
    just test
    @echo "Pre-push checks passed."
