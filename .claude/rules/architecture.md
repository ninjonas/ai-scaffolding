## Architecture Principles

These principles apply to **both Python and TypeScript** code.

### SOLID Principles

- **Single Responsibility**: Each class/module has one reason to change. Split when responsibilities diverge.
- **Open/Closed**: Extend behavior through abstractions (protocols, interfaces), not by modifying existing code.
- **Liskov Substitution**: Subtypes must be substitutable for their base types without breaking behavior.
- **Interface Segregation**: Prefer small, focused interfaces over large ones. Clients should not depend on methods they don't use.
- **Dependency Inversion**: Depend on abstractions (protocols/interfaces), not concrete implementations. High-level modules must not import from low-level modules directly.

### Domain-Driven Design (DDD)

- Define a clear **domain layer** with entities, value objects, and domain services.
- Use **bounded contexts** to separate distinct areas of the domain.
- Establish **ubiquitous language** — domain terms in code must match terms used by stakeholders.
- Keep domain logic free of infrastructure concerns (no HTTP, no SQL, no filesystem in domain objects).
- Use **aggregates** to enforce consistency boundaries.
- Use **repositories** as the interface between domain and persistence.

### Patterns of Enterprise Application Architecture (PofEAA)

- **Repository Pattern**: Abstract data access behind a repository interface. Domain code never talks to the database directly.
- **Unit of Work**: Group related operations into a single transaction boundary.
- **Data Mapper**: Map between domain objects and persistence representations — domain objects must not know how they are stored.
- **Service Layer**: Encapsulate application use cases in service classes that orchestrate domain objects and infrastructure.
- **Domain Model**: Rich domain objects with behavior, not anemic data containers with getters/setters.

### How to apply

- New features start with the domain: define entities and behaviors before thinking about HTTP or storage.
- Infrastructure (database, APIs, file I/O) lives behind abstractions that the domain defines.
- Use dependency injection to wire infrastructure into application services (see `code-conventions.md`).
- Keep controllers/routes thin — delegate to service layer immediately.
- Services orchestrate agents via compiled graphs: complex workflows (multi-step, tools, routing) invoke agent graphs; simple domain operations use direct service logic.
- Compile agent graphs at app startup and inject into services via DI — never instantiate agents in service code.
- When refactoring, move toward these patterns incrementally — don't over-engineer simple CRUD.
