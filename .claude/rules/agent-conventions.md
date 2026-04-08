## Agent Conventions

### Folder structure

- Each agent is a flat package under `src/app/agents/<agent_name>/`
- Every agent folder contains: `__init__.py`, `graph.py`, `nodes.py`, `state.py`
- Agent-specific tools go in the agent's skill folder, not in the agent folder
- Shared tools go in `src/app/agents/tools/`

### Naming

- Agent folder names: `snake_case` (e.g., `chatbot`, `researcher`, `code_reviewer`)
- Graph variables: `<agent>_graph` (e.g., `chatbot_graph`)
- State classes: `<Agent>State` (e.g., `ChatbotState`)
- Node functions: `snake_case` verbs (e.g., `invoke_llm`, `run_tools`, `load_skills`)

### Orchestration

- Agents never import sibling agents — only an orchestrator (supervisor) composes them
- Imports flow downward: supervisor → sub-agents → tools/skills
- Use `Command(goto="agent_name")` for handoffs or direct subgraph composition
- Supervisor lives at `src/app/agents/supervisor/`

### Prompts

- All prompts are plain markdown files in `src/app/agents/prompts/`
- Shared system prompt: `prompts/system.md` (all agents inherit)
- Shared output format: `prompts/output_format.md`
- Agent-specific prompts: `prompts/<agent_name>/*.md`
- Load with `Path.read_text()` — no Jinja2, no `ChatPromptTemplate`
- Assembly: `system.md` + `persona.md` + rules + `output_format.md`

### Skills

- Each skill is a folder under `src/app/agents/skills/<skill_name>/`
- Required: `SKILL.md` (markdown instructions with YAML frontmatter)
- Optional: `tools.py` (LangChain `@tool` decorated functions)
- Skills are loaded progressively — agent sees catalog first, loads full instructions on demand
- The skill loader (`skills/loader.py`) exposes `load_skill` and `read_skill_file` as LangChain tools

### Rules

- Behavioral constraints live in `src/app/agents/rules/*.md`
- Loaded as system context at prompt assembly time
- Keep rules short and actionable

### LLM provider

- All LLM access goes through `src/app/shared/llm.py` factory
- Never instantiate `ChatOpenAI` directly in agent code
- Provider is configured via env vars (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`)
