#!/usr/bin/env bash
# Syncs .claude/ markdown into docs/ so MkDocs can serve them.
#   .claude/rules/        → docs/guidelines/
#   .claude/agents/       → docs/agents/
#   .claude/skills/       → docs/skills/
# Also regenerates the nav section in mkdocs.yml between BEGIN/END markers.
# Called automatically by docs recipes (start, restart, build).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MKDOCS_YML="$REPO_ROOT/mkdocs.yml"
NAV_LINES=""

# ── Helpers ───────────────────────────────────────────

# Extract the first markdown heading from a file, skipping YAML frontmatter.
extract_heading() {
    sed -n '/^---$/,/^---$/d; s/^#\{1,\} *//p' "$1" | head -1
}

# sync_flat <source_dir> <dest_dir> <nav_label> <index_title> <index_desc>
# Copies *.md from source into dest, generates index.md, appends nav lines.
sync_flat() {
    local src_dir="$1" dest_dir="$2" nav_label="$3" title="$4" description="$5"

    rm -rf "$dest_dir"
    mkdir -p "$dest_dir"

    local dest_rel="${dest_dir#"$REPO_ROOT"/docs/}"

    for src_file in "$src_dir"/*.md; do
        [ -f "$src_file" ] || continue
        cp "$src_file" "$dest_dir/"
    done

    # Generate index
    cat > "$dest_dir/index.md" <<EOF
# $title

$description

EOF

    # Build nav entries
    local nav_items=""
    nav_items+="      - Overview: ${dest_rel}/index.md\n"

    for f in "$dest_dir"/*.md; do
        [ "$(basename "$f")" = "index.md" ] && continue
        local basename_f heading
        basename_f="$(basename "$f")"
        heading="$(extract_heading "$f")"
        [ -z "$heading" ] && heading="${basename_f%.md}"
        echo "- [$heading]($basename_f)" >> "$dest_dir/index.md"
        nav_items+="      - ${heading}: ${dest_rel}/${basename_f}\n"
    done

    NAV_LINES+="  - ${nav_label}:\n${nav_items}"
}

# sync_skills <source_dir> <dest_dir> <nav_label> <index_title> <index_desc>
# Skills have SKILL.md inside subdirectories — flatten them.
sync_skills() {
    local src_dir="$1" dest_dir="$2" nav_label="$3" title="$4" description="$5"

    rm -rf "$dest_dir"
    mkdir -p "$dest_dir"

    local dest_rel="${dest_dir#"$REPO_ROOT"/docs/}"

    for skill_dir in "$src_dir"/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        local skill_name
        skill_name="$(basename "$skill_dir")"
        cp "$skill_dir/SKILL.md" "$dest_dir/${skill_name}.md"
    done

    # Generate index
    cat > "$dest_dir/index.md" <<EOF
# $title

$description

EOF

    # Build nav entries
    local nav_items=""
    nav_items+="      - Overview: ${dest_rel}/index.md\n"

    for f in "$dest_dir"/*.md; do
        [ "$(basename "$f")" = "index.md" ] && continue
        local basename_f heading
        basename_f="$(basename "$f")"
        heading="$(extract_heading "$f")"
        [ -z "$heading" ] && heading="${basename_f%.md}"
        echo "- [$heading]($basename_f)" >> "$dest_dir/index.md"
        nav_items+="      - ${heading}: ${dest_rel}/${basename_f}\n"
    done

    NAV_LINES+="  - ${nav_label}:\n${nav_items}"
}

# ── Sync files ────────────────────────────────────────

sync_flat \
    "$REPO_ROOT/.claude/rules" \
    "$REPO_ROOT/docs/guidelines" \
    "Guidelines" \
    "Coding Guidelines" \
    "Auto-generated from \`.claude/rules/\`. Defines how we write and organize code."

sync_flat \
    "$REPO_ROOT/.claude/agents" \
    "$REPO_ROOT/docs/agents" \
    "Agents" \
    "Agents" \
    "Auto-generated from \`.claude/agents/\`. Defines the specialized agents available in this project."

sync_skills \
    "$REPO_ROOT/.claude/skills" \
    "$REPO_ROOT/docs/skills" \
    "Skills" \
    "Skills" \
    "Auto-generated from \`.claude/skills/\`. Defines the skills (slash commands) available in this project."

# ── Update mkdocs.yml nav ─────────────────────────────

BEGIN_MARKER="  # BEGIN GENERATED NAV"
END_MARKER="  # END GENERATED NAV"

# Write nav to a temp file so awk can read it line-by-line
NAV_FILE="$(mktemp)"
printf '%b' "$NAV_LINES" > "$NAV_FILE"

# Replace everything between markers (inclusive) with generated nav
awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" -v navfile="$NAV_FILE" '
    $0 == begin {
        print
        while ((getline line < navfile) > 0) print line
        close(navfile)
        skip = 1
        next
    }
    $0 == end { skip = 0; print; next }
    !skip     { print }
' "$MKDOCS_YML" > "$MKDOCS_YML.tmp"
mv "$MKDOCS_YML.tmp" "$MKDOCS_YML"
rm -f "$NAV_FILE"

echo "Synced .claude/ → docs/{guidelines,agents,skills}/ and updated mkdocs.yml nav"
