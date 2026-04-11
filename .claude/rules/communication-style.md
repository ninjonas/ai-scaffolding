## Communication Style

Apply this tone when generating **PR descriptions, documents, and narrative outputs** (project descriptions, architecture explanations, decision rationale, etc.).

### Principles

- **Lead with intent**: state the point first, then support it. No long preambles.
- **Say it directly**: no softening language, no hedging, no "this might be worth considering."
- **Be concise but complete**: every sentence earns its place. Cut filler, not substance.
- **Avoid corporate tone**: no buzzwords, no passive voice padding, no "leveraging synergies."
- **Natural paragraphs**: prefer flowing prose over excessive bullet lists for narrative content.
- **No validation-seeking**: don't close with "hope this helps!" or explain why you made choices defensively.

### When it applies

| Output type | Apply |
| ----------- | ----- |
| PR titles and descriptions | Yes |
| Functional and technical docs | Yes — tone only, keep structure |
| Project or feature descriptions | Yes |
| Architecture / decision rationale | Yes |
| Inline code comments | No |
| Test names and error messages | No |

### What to avoid

- Over-explaining decisions as if justifying them to a skeptic
- Excessive bullet points where a paragraph reads better
- Filler phrases: "It's worth noting that...", "As you can see...", "In order to..."
- Closing affirmations: "Let me know if you have questions!", "Hope that clarifies things!"
- **Em-dashes**: never use em-dashes (`—`) in any output. Use commas, colons, or restructure the sentence.
