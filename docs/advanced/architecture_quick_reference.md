# Architecture Quick Reference

This is a quick visual reference for FastOpenAPI's architecture. For detailed explanation, see [Architecture](architecture.md).

## Three-Tier Design

```mermaid
graph LR
    A[BaseRouter<br/>Route Registration] --> B[BaseAdapter<br/>Request Pipeline]
    B --> C[FrameworkRouter<br/>Framework Integration]

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e8f5e9
```

## Component Composition

```mermaid
graph TB
    subgraph "Your Code"
        E[Endpoint Functions]
    end

    subgraph "FastOpenAPI Core"
        R[BaseRouter]
        A[BaseAdapter]
        F[FrameworkRouter]
    end

    subgraph "Specialized Components"
        EX[Extractors]
        PR[ParameterResolver]
        DR[DependencyResolver]
        RB[ResponseBuilder]
        OG[OpenAPIGenerator]
    end

    E -->|decorated by| R
    R -->|inherits| A
    A -->|inherits| F
    F -.uses.-> EX
    F -.uses.-> PR
    F -.uses.-> DR
    F -.uses.-> RB
    R -.uses.-> OG
```

## Request Flow

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant FW as Framework
    participant FR as FrameworkRouter
    participant EX as Extractor
    participant PR as ParameterResolver
    participant DR as DependencyResolver
    participant EP as Endpoint
    participant RB as ResponseBuilder

    C->>FW: HTTP Request
    FW->>FR: Route matched
    FR->>EX: Extract data
    EX-->>FR: RequestData
    FR->>PR: Resolve params
    PR->>DR: Resolve deps
    DR-->>PR: Dependencies
    PR-->>FR: kwargs
    FR->>EP: Call endpoint
    EP-->>FR: Result
    FR->>RB: Build response
    RB-->>FR: Response
    FR-->>FW: Framework response
    FW-->>C: HTTP Response
```

## Key Classes

| Class | Location | Responsibility |
|-------|----------|----------------|
| `BaseRouter` | `fastopenapi/core/router.py` | Route registration, OpenAPI generation |
| `BaseAdapter` | `fastopenapi/routers/base.py` | Request pipeline orchestration |
| `FrameworkRouter` | `fastopenapi/routers/{framework}/` | Framework integration (3 methods) |
| `BaseRequestDataExtractor` / `BaseAsyncRequestDataExtractor` | `fastopenapi/routers/extractors.py` | Extract data from requests (sync / async) |
| `ParameterResolver` | `fastopenapi/resolution/resolver.py` | Parameter validation |
| `DependencyResolver` | `fastopenapi/core/dependency_resolver.py` | Dependency injection |
| `ResponseBuilder` | `fastopenapi/response/builder.py` | Response serialization |
| `OpenAPIGenerator` | `fastopenapi/openapi/generator.py` | Schema generation |

## Adding a Framework: Checklist

To add a new framework, implement:

- [ ] **Extractor class** - Extract data from framework request
  - Inherit from `BaseAsyncRequestDataExtractor` or `BaseRequestDataExtractor`
  - Implement `_get_*` methods (`_get_path_params`, `_get_query_params`, `_get_headers`, `_get_cookies`, `_get_body`, `_get_form_data`, `_get_files`)

- [ ] **Router class** - Integrate with framework
  - Inherit from `BaseAdapter`
  - Set `extractor_cls` or `extractor_async_cls`
  - Implement `add_route()`
  - Implement `build_framework_response()`
  - Implement `is_framework_response()`

- [ ] **Tests** - Comprehensive test suite
  - Router tests
  - Extractor tests
  - Integration tests

That's it! Just 2-3 classes.

## Parameter Hierarchy

```mermaid
classDiagram
    FieldInfo <|-- BaseParam
    BaseParam <|-- Param
    BaseParam <|-- Body
    Param <|-- Query
    Param <|-- Path
    Param <|-- Header
    Param <|-- Cookie
    Body <|-- Form
    Body <|-- File
```

## Error Hierarchy

```mermaid
classDiagram
    Exception <|-- APIError
    APIError <|-- BadRequestError
    APIError <|-- ValidationError
    APIError <|-- AuthenticationError
    APIError <|-- AuthorizationError
    APIError <|-- ResourceNotFoundError
    APIError <|-- InternalServerError
    InternalServerError <|-- DependencyError
    DependencyError <|-- CircularDependencyError
    DependencyError <|-- SecurityError
```

## Caching Strategy

| Cache | Type | Key | Cleanup | Purpose |
|-------|------|-----|---------|---------|
| TypeAdapter | Class-level | Model type | Never | Response validation |
| Signature | Class-level | Function | Never | Parameter inspection |
| Param Model | Class-level | Fields hash | Never | Validation models |
| Dependency | Request-scoped | (func, request) | Automatic (WeakKeyDictionary) | DI results |
| OpenAPI Schema | Instance-level | N/A | Never | Schema generation |

## Performance Optimizations

1. **Lazy OpenAPI Generation** - Schema only generated when accessed
2. **TypeAdapter Caching** - Pydantic adapters cached with thread-safe locking
3. **Signature Caching** - Function signatures cached
4. **Dynamic Model Caching** - Validation models cached per endpoint
5. **Request-Scoped Caching** - Dependencies cached per request
6. **Double-Checked Locking** - Fast path avoids locks for cache hits

## Design Principles

```mermaid
mindmap
  root((FastOpenAPI<br/>Design))
    Framework Agnostic
      Core never touches framework code
      Thin adapters
    Composition
      Specialized components
      Single responsibility
      Easy to test
    Type Safety
      Full type hints
      Pydantic v2
      TypeAdapter
    Thread Safety
      Locked caches
      WeakKeyDictionary
      Per-function locks
    Performance
      Multiple cache layers
      Lazy generation
      Minimal overhead
    Minimal Dependencies
      Pydantic v2 only
      Optional framework deps
```

## Next Steps

- [Full Architecture Documentation](architecture.md) - Detailed explanation
- [Custom Routers](custom_routers.md) - Build custom framework adapters
- [OpenAPI Customization](openapi_customization.md) - Customize schemas
- [Testing](testing.md) - Testing strategies
- [Performance](performance.md) - Optimization tips
