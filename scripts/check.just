set working-directory := '..'

# Run all convention checks
all: lines di literal-strings

# Check file and method line limits
lines *args:
    bash scripts/lib/check_lines.sh {{args}}

# Check dependency injection (Python only)
di *args:
    uv run python scripts/lib/check_di.py {{args}}

# Check for repeated literal strings
literal-strings *args:
    uv run python scripts/lib/check_literal_strings.py {{args}}
