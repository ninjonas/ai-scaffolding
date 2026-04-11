## Data Mapper Patterns

### Problem

Controllers/routes perform manual data transformations inline:

- Dict construction: `{"user_id": request.user_id, "name": request.name}`
- Manual field assignment and casting
- Validation and transformation logic scattered across route handlers
- DTO creation duplicated across multiple endpoints
- Makes routes stateful and untestable; violates PofEAA

This violates the **Data Mapper** pattern from PofEAA and **Data Transfer Object (DTO)** principles.

### Mandatory Patterns

#### 1. Dedicated Mapper Module for Each Concern

All data transformations must live in `src/app/infrastructure/mappers/`:

```
src/app/infrastructure/mappers/
├── __init__.py
├── conversation.py        # Domain ↔ Persistence
├── user.py               # DTO ↔ Domain
├── agent_results.py      # Agent output ↔ Domain (NEW)
├── voice_requests.py     # Voice API request ↔ Domain (NEW)
└── chat_requests.py      # Chat API request ↔ Domain (NEW)
```

**Never place mappers in:**

- `src/app/api/` (routes)
- `src/app/service/` (services)
- Inline in handler functions

**Exception:** Result mappers for agent output (e.g., `chat_result_mapper` in `src/app/service/mappers.py`) are co-located with services because they're part of the orchestration contract.

#### 2. Mapper Naming & Type Hints

```python
# GOOD: Clear intent and types
class UserRequestMapper:
    @staticmethod
    def to_domain(dto: CreateUserRequest) -> User:
        """Transform DTO to domain entity."""
        return User(name=dto.name, email=dto.email)

    @staticmethod
    def to_dto(entity: User) -> UserResponse:
        """Transform domain entity to response DTO."""
        return UserResponse(id=entity.id, name=entity.name, email=entity.email)

# BAD: Inline lambda or dict construction
user = {"id": entity.id, "name": entity.name}  # ← Should be in mapper
```

#### 3. Routes/Services Delegate to Mappers

```python
# GOOD: Route delegates transformation
@router.post("/users/")
async def create_user(req: CreateUserRequest, svc: UserService) -> UserResponse:
    """Create user via application service."""
    user = await svc.create(UserRequestMapper.to_domain(req))
    return UserRequestMapper.to_dto(user)

# BAD: Inline transformation
@router.post("/users/")
async def create_user(req: CreateUserRequest, svc: UserService) -> UserResponse:
    user = await svc.create(User(name=req.name, email=req.email))  # ← Use mapper
    return UserResponse(id=user.id, name=user.name, email=user.email)  # ← Use mapper
```

#### 4. Mapper Invariants

- **Pure functions**: No I/O, no side effects, deterministic
- **Type hints**: Full `(InputType) -> OutputType`
- **Bidirectional**: Mappers support `to_domain()` and `to_dto()` / `to_model()` pairs
- **No business logic**: Transformation only; domain logic stays in entities/services
- **Immutable input**: Do not mutate passed-in objects

```python
# GOOD: Pure, reversible
def request_to_domain(dto: RequestDTO) -> DomainEntity:
    return DomainEntity(field1=dto.field1, field2=dto.field2)

def domain_to_response(entity: DomainEntity) -> ResponseDTO:
    return ResponseDTO(field1=entity.field1, field2=entity.field2)

# BAD: Side effects, non-reversible
def request_to_domain(dto: RequestDTO) -> DomainEntity:
    dto.processed = True  # ← Mutates input
    log.info(f"Creating {dto.name}")  # ← Side effect in mapper
    send_external_event(dto)  # ← Side effect
    return DomainEntity(...)
```

### Checked by

- `scripts/lib/check_mapper_patterns.py` — AST-based validator
- Run via `just check-mapper-patterns`
- Run via `just check` (aggregated)
- Git pre-commit hook enforces (via `just git-pre-commit`)

### Enforcement

| Violation                                             | Severity |
| ----------------------------------------------------- | -------- |
| Dict/DTO construction in `src/app/api/`               | WARN     |
| Dict/DTO construction in `src/app/service/`           | WARN     |
| Mapper file outside `src/app/infrastructure/mappers/` | FAIL     |
| Inline dataclass instantiation in route handler       | WARN     |
| Result mapper as inline lambda (agent output)         | WARN     |

### See Also

- [Architecture Rules: PofEAA Patterns](./architecture.md#patterns-of-enterprise-application-architecture-pofeaa)
- [Code Conventions: File Organization](./code-conventions.md)
