set working-directory := '..'

# Run all convention checks
all: lines di literal-strings mapper-patterns service-patterns

# Check file and method line limits
lines *args:
    bash scripts/lib/check_lines.sh {{args}}

# Check dependency injection (Python only)
di *args:
    uv run python scripts/lib/check_di.py {{args}}

# Check for repeated literal strings
literal-strings *args:
    uv run python scripts/lib/check_literal_strings.py {{args}}

# Check for proper data mapper usage patterns
mapper-patterns *args:
    uv run python scripts/lib/check_mapper_patterns.py {{args}}

# Check for proper service layer patterns
service-patterns *args:
    uv run python scripts/lib/check_service_patterns.py {{args}}
