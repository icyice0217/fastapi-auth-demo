

# FastAPI (Python 3.12) Production Best Practices Guide

## 1. Project Structure Standards

Recommended layered modular structure, fully aligning with the original Java BFF layering logic:
```
your_bff_project/
├── main.py                # Service entry point; only mounts routers and global middleware
├── pyproject.toml         # Locks Python version >=3.12,<3.13
├── requirements.txt       # Dependency list; all packages compatible with Python 3.12
├── app/
│   ├── __init__.py
│   ├── routers/           # Split routers by business domain; manage with APIRouter
│   │   ├── user.py
│   │   └── order.py
│   ├── services/          # Business logic layer; corresponds to Java Service layer
│   ├── models/            # Pydantic data models; corresponds to Java DTO/POJO
│   ├── dependencies/      # Dependency injection logic (auth, rate limiting, etc.)
│   ├── utils/             # Utility functions; corresponds to Java Utils classes
│   └── data/              # Resource files directory (JSON/configs); loaded via importlib.resources
```

## 2. Routing and Performance Optimization

- **Modular Routers**: Do NOT stack all endpoints in `main.py`. Split by business domain using `APIRouter`. Inject only necessary dependencies per module to avoid global overhead from irrelevant middleware.
- **Async First**: All I/O operations (HTTP requests, DB queries) MUST be defined with `async def`, paired with async clients like `httpx`/`asyncpg` to leverage FastAPI's asynchronous performance.
- **Route Order**: Place fixed routes before dynamic routes to prevent matching logic conflicts.

## 3. Data Validation Standards

- All request bodies and response bodies MUST use **Pydantic v2** `BaseModel` for automatic type conversion and validation, replacing Java Jackson serialization logic.
- Avoid manual null-checking in business logic. Use Pydantic's `Field` validation rules (`gt`, `min_length`, etc.) to automatically intercept invalid requests.

## 4. Dependency Injection and Security

- Use FastAPI's native `Depends()` for cross-cutting concerns like authentication, logging, and rate limiting, completely replacing Spring's `@Autowired` mechanism.
- Configure CORS explicitly in production. Specify allowed origins; NEVER use `allow_origins=["*"]` to expose the service.
- Integrate OAuth2 + JWT for API identity authentication; avoid passing sensitive parameters in plain text.

## 5. Resource and Deployment Standards

- All internal resource files (JSON/configs) MUST be loaded via `importlib.resources.files()`. Do NOT use `__file__` based path joining to ensure resources are accessible when packaged as WHEEL/ZIP.
- Deploy using `Uvicorn + Gunicorn` with multiple worker processes to utilize multi-core CPU resources.
- Enable auto-generated Swagger UI documentation but restrict access to internal networks; disable it for public-facing services.

## 6. Code Style Requirements

- Strictly follow PEP 8 coding standards; use `ruff` for automatic formatting.
- Add Google-style docstrings to all public methods, clearly describing parameters, return values, and exceptions.
- Do NOT import legacy generic types like `typing.List` or `typing.Dict`. Use Python 3.12 native generic syntax `list[T]`/`dict[K, V]`.
