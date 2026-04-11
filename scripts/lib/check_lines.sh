#!/usr/bin/env bash
# Check Python and TypeScript files for line-count limits.
#
# Limits:
#   - Source files (py/ts/tsx): 200 lines max, warn at 160+
#   - Test files (test_*.py, *.test.ts, *.test.tsx): 500 lines max, warn at 400+
#   - Methods/functions: 50 lines max, warn at 40+
#
# Usage:
#   check_lines.sh [file ...]          # check specific files
#   check_lines.sh                     # check all src/ files

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Limits
SOURCE_MAX=200
SOURCE_WARN=160
TEST_MAX=500
TEST_WARN=400
METHOD_MAX=50
METHOD_WARN=40

is_test_file() {
    local base
    base="$(basename "$1")"
    [[ "$base" == test_* ]] || [[ "$base" == *.test.ts ]] || [[ "$base" == *.test.tsx ]] || [[ "$base" == *.spec.ts ]] || [[ "$base" == *.spec.tsx ]]
}

# Collect files
files=()
if (( $# > 0 )); then
    for arg in "$@"; do
        if [[ -f "$arg" ]]; then
            files+=("$arg")
        elif [[ -f "$REPO_ROOT/$arg" ]]; then
            files+=("$REPO_ROOT/$arg")
        else
            echo -e "${YELLOW}Warning: Skipping $arg (not found)${NC}" >&2
        fi
    done
else
    while IFS= read -r -d '' f; do
        files+=("$f")
    done < <(find "$REPO_ROOT/src" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) \
        -not -path '*/__pycache__/*' -not -path '*/node_modules/*' -not -path '*/dist/*' -print0)
fi

if (( ${#files[@]} == 0 )); then
    echo "No files to check."
    exit 0
fi

echo "Checking line limits..."

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

# --- File length checks ---
for file in "${files[@]}"; do
    line_count="$(wc -l < "$file" | tr -d '[:space:]')"
    rel_path="${file#"$REPO_ROOT/"}"

    if is_test_file "$file"; then
        max=$TEST_MAX; warn=$TEST_WARN; label="test file"
    else
        max=$SOURCE_MAX; warn=$SOURCE_WARN; label="source file"
    fi

    if (( line_count > max )); then
        echo -e "  ${RED}FAIL${NC} ${rel_path}: ${line_count} lines (max ${max} for ${label})" >> "$tmpfile"
    elif (( line_count > warn )); then
        echo -e "  ${YELLOW}WARN${NC} ${rel_path}: ${line_count} lines (approaching ${max} limit for ${label})" >> "$tmpfile"
    fi
done

# --- Python method length checks ---
# Uses awk with POSIX-compatible match() (no capture groups)
for file in "${files[@]}"; do
    [[ "$file" == *.py ]] || continue
    rel_path="${file#"$REPO_ROOT/"}"

    awk -v rel_path="$rel_path" -v max="$METHOD_MAX" -v warn="$METHOD_WARN" '
    function first_param_open(line,    start) {
        if (!match(line, /def[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/)) return 0
        return RSTART + RLENGTH - 1
    }
    function paren_delta_from(line, pos,    i, c, d) {
        d = 0
        for (i = pos; i <= length(line); i++) {
            c = substr(line, i, 1)
            if (c == "(") d++
            if (c == ")") d--
        }
        return d
    }
    function paren_delta_line(line,    i, c, d) {
        d = 0
        for (i = 1; i <= length(line); i++) {
            c = substr(line, i, 1)
            if (c == "(") d++
            if (c == ")") d--
        }
        return d
    }
    function header_complete_after_sig(line,    i, last_rp) {
        last_rp = 0
        for (i = 1; i <= length(line); i++) {
            if (substr(line, i, 1) == ")") last_rp = i
        }
        if (last_rp == 0) return 0
        return (substr(line, last_rp) ~ /^\)[[:space:]]*(->.*)?:/)
    }
    /^[[:space:]]*def[[:space:]]+[a-zA-Z_]/ {
        if (func_name != "" && func_lines > 0 && !in_sig) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
        }
        # Extract function name: find "def " then grab the word after it
        s = $0
        sub(/^[[:space:]]*def[[:space:]]+/, "", s)
        sub(/[^a-zA-Z0-9_].*/, "", s)
        func_name = s
        func_start = NR
        func_lines = 0
        # Capture indentation of the def line
        match($0, /^[[:space:]]*/)
        func_indent = RLENGTH
        op = first_param_open($0)
        if (op > 0) {
            sig_depth = paren_delta_from($0, op)
        } else {
            sig_depth = 0
        }
        if (sig_depth == 0 && header_complete_after_sig($0)) {
            in_sig = 0
        } else {
            in_sig = 1
        }
        next
    }
    /^[[:space:]]*class[[:space:]]+[A-Za-z_]/ {
        if (func_name != "" && !in_sig) {
            match($0, /^[[:space:]]*/)
            if (RLENGTH <= func_indent) {
                if (func_lines > 0) {
                    printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
                }
                func_name = ""
                func_lines = 0
                next
            }
        } else {
            next
        }
    }
    func_name != "" && in_sig {
        if (/^[[:space:]]*$/) next
        if (/^[[:space:]]*#/) next
        sig_depth += paren_delta_line($0)
        if (sig_depth <= 0 && header_complete_after_sig($0)) {
            in_sig = 0
            sig_depth = 0
        }
        next
    }
    func_name != "" && !in_sig {
        if (/^[[:space:]]*$/) next
        if (/^[[:space:]]*#/) next
        match($0, /^[[:space:]]*/)
        cur_indent = RLENGTH
        if (cur_indent <= func_indent) {
            if (func_lines > 0) {
                printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
            }
            func_name = ""
            func_lines = 0
        } else {
            func_lines++
        }
    }
    END {
        if (func_name != "" && func_lines > 0 && !in_sig) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
        }
    }
    ' "$file" | while IFS=: read -r rp line_no name lines; do
        if (( lines > METHOD_MAX )); then
            echo -e "  ${RED}FAIL${NC} ${rp}:${line_no}: function '${name}' is ${lines} lines (max ${METHOD_MAX})" >> "$tmpfile"
        elif (( lines > METHOD_WARN )); then
            echo -e "  ${YELLOW}WARN${NC} ${rp}:${line_no}: function '${name}' is ${lines} lines (approaching ${METHOD_MAX} limit)" >> "$tmpfile"
        fi
    done
done

# --- TypeScript method length checks ---
# Uses brace-depth tracking
for file in "${files[@]}"; do
    [[ "$file" == *.ts || "$file" == *.tsx ]] || continue
    rel_path="${file#"$REPO_ROOT/"}"

    awk -v rel_path="$rel_path" '
    /^[[:space:]]*(export[[:space:]]*)?(async[[:space:]]*)?(function)[[:space:]]/ && /\{/ {
        if (func_name != "" && func_lines > 0) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
        }
        s = $0
        sub(/.*function[[:space:]]+/, "", s)
        sub(/[^a-zA-Z0-9_].*/, "", s)
        if (s != "") {
            func_name = s; func_start = NR; func_lines = 0; brace_depth = 0
            for (i = 1; i <= length($0); i++) {
                c = substr($0, i, 1)
                if (c == "{") brace_depth++; if (c == "}") brace_depth--
            }
            in_func = (brace_depth > 0) ? 1 : 0
        }
        next
    }
    /^[[:space:]]*(export[[:space:]]*)?(const|let|var)[[:space:]]/ && /=>/ {
        if (func_name != "" && func_lines > 0) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
        }
        s = $0
        sub(/.*\y(const|let|var)[[:space:]]+/, "", s)
        sub(/[^a-zA-Z0-9_].*/, "", s)
        if (s != "") {
            func_name = s; func_start = NR; func_lines = 0; brace_depth = 0
            for (i = 1; i <= length($0); i++) {
                c = substr($0, i, 1)
                if (c == "{") brace_depth++; if (c == "}") brace_depth--
            }
            in_func = (brace_depth > 0) ? 1 : 0
        }
        next
    }
    in_func == 1 {
        if (/^[[:space:]]*$/) next
        if (/^[[:space:]]*\/\//) next
        func_lines++
        for (i = 1; i <= length($0); i++) {
            c = substr($0, i, 1)
            if (c == "{") brace_depth++; if (c == "}") brace_depth--
        }
        if (brace_depth <= 0) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
            func_name = ""; func_lines = 0; in_func = 0
        }
    }
    END {
        if (func_name != "" && func_lines > 0) {
            printf "%s:%d:%s:%d\n", rel_path, func_start, func_name, func_lines
        }
    }
    ' "$file" | while IFS=: read -r rp line_no name lines; do
        if (( lines > METHOD_MAX )); then
            echo -e "  ${RED}FAIL${NC} ${rp}:${line_no}: function '${name}' is ${lines} lines (max ${METHOD_MAX})" >> "$tmpfile"
        elif (( lines > METHOD_WARN )); then
            echo -e "  ${YELLOW}WARN${NC} ${rp}:${line_no}: function '${name}' is ${lines} lines (approaching ${METHOD_MAX} limit)" >> "$tmpfile"
        fi
    done
done

# --- Print results ---
output=$(cat "$tmpfile")
errors=$(echo "$output" | grep -c "FAIL" || true)
warnings=$(echo "$output" | grep -c "WARN" || true)

if [[ -n "$output" ]]; then
    echo "$output"
fi

WARN_THRESHOLD=15

if (( errors > 0 )); then
    echo ""
    echo -e "${RED}${errors} error(s) and ${warnings} warning(s) found.${NC}"
    exit 1
elif (( warnings >= WARN_THRESHOLD )); then
    echo ""
    echo -e "${RED}${warnings} warning(s) found — threshold of ${WARN_THRESHOLD} exceeded.${NC}"
    exit 1
elif (( warnings > 0 )); then
    echo ""
    echo -e "${YELLOW}${warnings} warning(s) found (no errors).${NC}"
    exit 0
else
    echo -e "${GREEN}All files within line limits.${NC}"
    exit 0
fi
