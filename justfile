# Root justfile — single entry point for all dev tasks.
# Delegates to child justfiles in scripts/ for SRP.

set dotenv-load

API_PORT := env("API_PORT", "8000")
WEB_PORT := env("WEB_PORT", "3000")
DOCS_PORT := env("DOCS_PORT", "8100")

# Default: show available recipes
default:
    @just --list

# ── Python ────────────────────────────────────────
lint-py *args:
    just -f scripts/lint.just py {{args}}

test-py *args:
    just -f scripts/test.just py {{args}}

fmt-py *args:
    just -f scripts/fmt.just py {{args}}

# ── TypeScript ────────────────────────────────────
lint-ts *args:
    just -f scripts/lint.just ts {{args}}

test-ts *args:
    just -f scripts/test.just ts {{args}}

fmt-ts *args:
    just -f scripts/fmt.just ts {{args}}

build-web:
    just -f scripts/dev.just build-web

# ── Markdown ──────────────────────────────────────
lint-md *args:
    just -f scripts/lint.just md {{args}}

fmt-md *args:
    just -f scripts/fmt.just md {{args}}

# ── All ───────────────────────────────────────────
lint: lint-py lint-ts lint-md

test: test-py test-ts

fmt: fmt-py fmt-ts fmt-md

# ── Dev ───────────────────────────────────────────
dev-start:
    just -f scripts/dev.just start

dev-stop:
    just -f scripts/dev.just stop

dev-restart:
    just -f scripts/dev.just restart

# ── Docs ──────────────────────────────────────────
docs-start *args:
    just -f scripts/docs.just start {{args}}

docs-stop:
    just -f scripts/docs.just stop

docs-restart:
    just -f scripts/docs.just restart

docs-build *args:
    just -f scripts/docs.just build {{args}}

# ── Checks ────────────────────────────────────────
check: check-lines check-di check-literal-strings check-mapper-patterns check-service-patterns

check-lines *args:
    just -f scripts/check.just lines {{args}}

check-di *args:
    just -f scripts/check.just di {{args}}

check-literal-strings *args:
    just -f scripts/check.just literal-strings {{args}}

check-mapper-patterns *args:
    just -f scripts/check.just mapper-patterns {{args}}

check-service-patterns *args:
    just -f scripts/check.just service-patterns {{args}}

# ── Code Review ───────────────────────────────────
code-review:
    just -f scripts/review.just all

# ── Code generation ───────────────────────────────
gen-types:
    just -f scripts/gen.just types

# ── Git Hooks ─────────────────────────────────────
git-pre-commit:
    just -f scripts/git.just pre-commit

git-pre-push:
    just -f scripts/git.just pre-push

# ── Utilities ─────────────────────────────────────
kill port:
    just -f scripts/dev.just kill {{port}}

# ── Clean ─────────────────────────────────────────
bsc:
    just -f scripts/clean.just bsc

# ── Setup ─────────────────────────────────────────
setup:
    just -f scripts/setup.just all

setup-statusbar scope='project':
    just -f scripts/setup.just claude-statusbar {{scope}}

# ── Fork ──────────────────────────────────────
fork *args:
    just -f scripts/fork.just fork {{args}}

# ── Database ──────────────────────────────────────
db-reset:
    just -f scripts/db.just reset

db-tables:
    just -f scripts/db.just tables

db-counts:
    just -f scripts/db.just counts

db-chroma-stats:
    just -f scripts/db.just chroma-stats

db-sqlite *args:
    just -f scripts/db.just sqlite {{args}}

test-rag-e2e:
    just -f scripts/db.just test-rag-e2e
