## Project structure

- `src/app/` — Python application root
  - `src/app/api/` — FastAPI routes, DTOs, data mappers (thin controllers)
  - `src/app/agents/` — LangGraph agent system (graphs, prompts, skills, rules, tools)
  - `src/app/domain/` — domain entities, value objects, repository protocols (DDD)
  - `src/app/infrastructure/` — SQLAlchemy models, repository impls, data mappers, unit of work (PofEAA)
  - `src/app/service/` — application service layer (PofEAA)
  - `src/app/shared/` — cross-cutting: config, LLM factory, logging, DI
- `src/web/` — Vite React TypeScript frontend
- `src/tests/` — Python tests (pytest)
- `scripts/` — child justfiles (one per concern, SRP)
- `scripts/lib/` — shell/Python scripts supporting just recipes
- `docs/` — documentation (MkDocs site)
- `docs/plans/` — design docs and implementation plans
- `logs/` — log output
- `tmp/` — scratch / spike output (gitignored contents)
