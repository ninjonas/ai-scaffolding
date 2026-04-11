## Diagrams

- Use **Mermaid** for all diagrams in documentation
- Embed diagrams as fenced code blocks with the `mermaid` language tag
- Choose diagram type by purpose:
  - `flowchart LR/TD` — system flows, data pipelines, decision trees
  - `sequenceDiagram` — request/response flows, service interactions
  - `classDiagram` — domain model relationships
  - `graph` — generic node-edge relationships
- Keep each diagram focused on a single concern — split if it grows complex
- Label all nodes clearly; avoid abbreviations unless defined in surrounding text
- Do not use external diagram tools (Draw.io, Lucidchart, PlantUML)
- **Functional docs**: one high-level flowchart showing the user-visible system flow
- **Technical docs**: component diagram + sequence diagram (minimum)
