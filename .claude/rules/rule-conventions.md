## Rule conventions

### Size and split

- Rule files must stay **under 50 lines** (including headings and lists).
- If a rule outgrows that limit, move the **detailed how-to workflow** into a **companion skill** under `.claude/skills/`.
- **Rules** say **what**: constraints, intent, and structure agents must follow.
- **Skills** say **how**: step-by-step procedures, templates, and workflows.

### Naming and location

- Rules live in `.claude/rules/` as **kebab-case** `.md` files (e.g. `documents.md`).
- The companion skill for a rule uses the **same base name** as the rule (filename without `.md`), as a directory under `.claude/skills/<base-name>/` with `SKILL.md` inside.

### Referencing skills

- When a rule points agents at a skill, add an inline pointer: `See skill: <name>` (skill directory / frontmatter `name`, e.g. `create-doc`).
