---
name: create-rule
description: Create a new rule file (and optional companion skill) in .claude/rules/ following project conventions. Use when asked to add, document, or enforce a new constraint or convention.
argument-hint: "<rule-name>"
---

# Create Rule

Creates a kebab-case rule file under `.claude/rules/` (≤50 lines), optionally paired with a companion skill when workflow detail is needed.

## Workflow

### Step 1: Audit existing rules

```bash
wc -l .claude/rules/*.md | sort -n
```

- Note current line counts to understand what already exists and detect any rules already over the limit.
- Check whether a rule covering the same topic already exists — update instead of creating a duplicate.

### Step 2: Classify the new content

| Content type | Where it goes |
|---|---|
| Constraints, naming conventions, what is required/forbidden | Rule file (`.claude/rules/<name>.md`) |
| Step-by-step workflow, templates, decision trees | Companion skill (`.claude/skills/<name>/SKILL.md`) |
| Both constraints **and** detailed procedure | Rule file (thin) + companion skill (full procedure) |

A rule answers **what**. A skill answers **how**.

### Step 3: Create the rule file

- Path: `.claude/rules/<kebab-case-name>.md`
- No YAML frontmatter required — start directly with a `## <Title>` heading.
- State constraints, naming requirements, and intent clearly.
- Keep it **under 50 lines** (headings and blank lines count).
- If a companion skill will exist, add at the bottom:

  ```
  See skill: <name>
  ```

### Step 4: Create a companion skill (if needed)

Only create a companion skill when the rule requires procedural detail that would push the rule past 50 lines.

- Path: `.claude/skills/<same-base-name>/SKILL.md`
- Use this frontmatter template:

  ```markdown
  ---
  name: <kebab-case-name>
  description: <One sentence. State when an agent should invoke this skill.>
  argument-hint: "<placeholder>"
  ---
  ```

- Follow the frontmatter with `# <Title>` and `## Workflow` sections.
- No line-count limit on skill files.

### Step 5: Verify line count

```bash
wc -l .claude/rules/<new-rule>.md
```

The rule file must report **≤50 lines**. If it exceeds 50:

1. Move procedural content into a companion skill (Step 4).
2. Replace that content in the rule with a `See skill: <name>` pointer.
3. Re-run `wc -l` to confirm compliance.

### Step 6: Confirm outputs

- [ ] `.claude/rules/<name>.md` exists and is ≤50 lines.
- [ ] If a skill was created: `.claude/skills/<name>/SKILL.md` exists with valid frontmatter.
- [ ] Rule file ends with `See skill: <name>` when a companion skill exists.
- [ ] No unrelated files were modified.
