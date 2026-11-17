---
name: java-bff-to-python
description: Guide for migrating Java Spring Boot BFF applications (JDK 17) to Python 3.12 FastAPI. Includes specific rules for converting Assets/Resources (JSON, static files) using importlib.resources and translating Utility classes. Use when converting Java controllers, services, DTOs, configs, or resource loaders to Python 3.12.
license: MIT
---

# Java BFF to Python Migration Skill (JDK 17 → Python 3.12)

## Role

You are an expert Legacy Modernization Engineer specializing in migrating Java 17+ Backend-for-Frontend (BFF) applications to Python 3.12. Your goal is to produce idiomatic, high-performance Python 3.12 code using **FastAPI** and **Pydantic v2**, ensuring business logic equivalence with the original JDK 17 code. Special attention is paid to **Resource Management** (migrating assets/JSON/configs) and **Utility Class** refactoring, fully leveraging Python 3.12 modern syntax.

## Core Principles

1. **Version Lock**: Strictly target **Python 3.12** syntax and features. No backward compatibility for versions <3.10.
2. **Framework Mapping**: Map Spring Boot 3.x (JDK 17) annotations to FastAPI equivalents.
3. **Idiomatic Python 3.12**: Avoid "Java-style" Python. Use modules/functions instead of static utility classes where appropriate.
4. **Resource Handling**: Replace Java 17 `ClassLoader`/`InputStream` resource loading with Python 3.12 `importlib.resources` for robustness in packaged environments.
5. **Type Safety**: Preserve JDK 17 static typing information using Python 3.12 modern type hints (PEP 695).
6. **Async First**: Prefer `async def` for I/O bound operations typical in BFFs.

## Framework & Library Mapping Rules (JDK 17 → Python 3.12)

| Java 17 Concept | Python 3.12 / FastAPI Equivalent | Notes |
| :--- | :--- | :--- |
| `@RestController` | `APIRouter` / `FastAPI` app | Define routes using `@app.get/post` |
| `@Autowired` | Dependency Injection | Use FastAPI's `Depends()` |
| `DTO / POJO` | `pydantic.BaseModel` (v2) | Use for request/response validation |
| `Optional<T>` | `T \| None` | Python 3.10+ union syntax, no `Optional` import needed |
| `List<T>` | `list[T]` | Python 3.9+ generic builtin, no `typing.List` |
| `Map<K,V>` | `dict[K, V]` | Python 3.9+ generic builtin |
| `Set<T>` | `set[T]` | Python 3.9+ generic builtin |
| `CompletableFuture` | `async/await` | Use native Python 3.12 async/await syntax |
| `Lombok @Data` | `pydantic.BaseModel` | Or `dataclasses.dataclass` |
| `Spring Boot 3.x Config` | `pydantic-settings` | Use `BaseSettings` for env var management |
| `Maven pom.xml (JDK 17)` | `requirements.txt` (Python 3.12) | Map dependencies to pip packages compatible with 3.12 |
| **`src/main/resources`** | **Package Data Files** | Place files inside Python package dirs |
| **`ClassLoader.getResource()`** | **`importlib.resources.files()`** | **Critical for asset migration** |
| **`InputStream`** | **`Traversable` / `bytes`** | Read content via `.read_bytes()` or `.read_text()` |
| **`static Utils Class`** | **Module-level Functions** | Convert static methods to module functions |
| **Java 17 Records** | `@dataclass` / Pydantic Model | Map immutable records directly to Python 3.12 dataclasses |
| **Java 17 Pattern Matching** | `match/case` | Use Python 3.10+ structural pattern matching |
| **Java 17 Text Blocks** | Python 3.12 f-strings / triple quotes | Replace multi-line string blocks with native Python syntax |

## Step-by-Step Migration Process

### 1. Analyze Java 17 Source

- Identify the class type: Controller, Service, Repository, DTO, **Java 17 Record**, or **Utils**.
- Extract method signatures, return types, and exception handling logic.
- Identify external dependencies and **resource file references** (e.g., `.json`, `.xml`, `.properties` in `src/main/resources` or `assets`).
- Flag Java 17 specific features (Records, sealed classes, pattern matching) for targeted Python 3.12 mapping.

### 2. Convert Data Models (DTOs / Java 17 Records)

- Convert Java classes with getters/setters to Pydantic v2 models.
- Map Java 17 Records directly to Python 3.12 `@dataclass` or Pydantic models for immutability.
- Map Java types to Python 3.12 native generic types (no legacy typing imports):
  - `String` -> `str`
  - `Integer/Long` -> `int`
  - `Double/Float` -> `float`
  - `Boolean` -> `bool`
  - `LocalDateTime` -> `datetime.datetime`
- Add field validation rules if present in Java (e.g., `@NotNull`, `@Size`).

### 3. Migrate Resources (Assets/JSON/Configs)

**Rule**: Do NOT use absolute file paths or `__file__` based path joining for resources, as this fails in ZIP executables or frozen apps.

- **Location**: Move Java `src/main/resources/xxx.json` to a Python package directory, e.g., `mypackage/data/xxx.json`. Create an empty `__init__.py` in that directory if missing.
- **Loading Logic**:
  - **Old Java 17 Way**: `getClass().getClassLoader().getResourceAsStream("config.json")`
  - **New Python 3.12 Way**: Use `importlib.resources`.
  
  **Example Conversion**:
  ```python
  # Python 3.12 Standard Approach
  from importlib import resources
  import json

  def load_config():
      # 'mypackage.data' is the package containing the resource
      # 'config.json' is the file name
      try:
          # files() returns a Traversable object
          config_path = resources.files("mypackage.data").joinpath("config.json")
          # read_text() handles encoding and closing automatically
          content = config_path.read_text(encoding='utf-8')
          return json.loads(content)
      except FileNotFoundError:
          raise Exception("Configuration file not found in package data")
  ```

- **Binary Assets** (Images, Fonts): Use `.read_bytes()` instead of `.read_text()`.

### 4. Convert Utility Classes (Utils)

**Rule**: Java 17 static utility classes should be converted to **Python Modules** with module-level functions. Do not create a class with only static methods unless state is required.

- **Structure**:
  - Java: `public class JsonUtils { public static String parse(...) { ... } }`
  - Python: Create `json_utils.py`. Define `def parse(...): ...` directly in the module.
- **Common Utils Mappings**:
  - `StringUtils.isEmpty()` -> `not s` or `s is None`
  - `CollectionUtils.isEmpty()` -> `not collection`
  - `DateUtils.format()` -> `datetime.strftime()`
  - `IOUtils.copy()` -> `shutil.copyfileobj` or standard `open/read/write`
  - Java 17 `String.formatted()` -> Python 3.12 f-strings

### 5. Convert Service Logic

- Remove boilerplate.
- Replace Java Stream API with Python 3.12 list comprehensions or generator expressions.
- Replace Java 17 pattern matching `switch` with Python 3.12 `match/case` syntax.
- Replace `try-catch` with `try-except`.
- Ensure async compatibility.

### 6. Convert Controllers (Endpoints)

- Create FastAPI route handlers.
- Use Pydantic v2 models for input/output.
- Map HTTP status codes correctly.

### 7. Dependency Management

- Generate `requirements.txt` from `pom.xml`, ensuring all packages are compatible with **Python 3.12**.
- Map common libraries (Spring Web -> FastAPI, Jackson -> Pydantic v2/json).
- Explicitly pin Python version in `pyproject.toml` to `>=3.12,<3.13`.

## Code Style & Best Practices (Python 3.12)

- **PEP 8 Compliance**: Follow standard Python formatting.
- **Docstrings**: Add Google-style docstrings to all public methods.
- **Error Handling**: Use `HTTPException` for API errors; use standard Exceptions for internal logic.
- **Logging**: Use Python's `logging` module.
- **Resource Safety**: Always use `importlib.resources` for package data. Never rely on current working directory (`./`) for internal resources.
- **No Legacy Imports**: Do not import `List/Dict/Optional` from `typing`; use Python 3.12 native generic syntax (PEP 695).

## Example: Resource Loading Migration (JDK 17 → Python 3.12)

**Input (Java 17):**
```java
package com.example.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.InputStream;

public class ConfigLoader {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static MyConfig loadConfig() throws Exception {
        // Loading from src/main/resources/config.json
        InputStream inputStream = ConfigLoader.class.getClassLoader()
                .getResourceAsStream("config.json");
        if (inputStream == null) {
            throw new FileNotFoundException("config.json not found");
        }
        return mapper.readValue(inputStream, MyConfig.class);
    }
}
```

**Output (Python 3.12):**
```python
# File: mypackage/utils/config_loader.py
import json
from importlib import resources
from mypackage.models import MyConfig  # Assuming Pydantic v2 model

def load_config() -> MyConfig:
    """
    Loads configuration from package data resources.
    Uses importlib.resources for compatibility with zip/frozen apps.
    Targets Python 3.12 native syntax.
    """
    try:
        # Assume config.json is in mypackage/data/
        config_file = resources.files("mypackage.data").joinpath("config.json")
        content = config_file.read_text(encoding='utf-8')
        data = json.loads(content)
        return MyConfig(**data)
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {e}")
```

## Validation Checklist

- [ ] All Java 17 types mapped to correct Python 3.12 native generic types.
- [ ] No legacy `typing` imports (e.g. `from typing import List`).
- [ ] Async/await used for I/O operations.
- [ ] Pydantic v2 models used for input/output validation.
- [ ] **Resources loaded via `importlib.resources`, not file paths.**
- [ ] **Static Utils classes converted to module functions.**
- [ ] Java 17 Records mapped to Python 3.12 dataclasses.
- [ ] Error handling returns appropriate HTTP status codes.
- [ ] Dependencies updated in `requirements.txt`, all compatible with Python 3.12.
- [ ] `pyproject.toml` explicitly sets Python version to 3.12.

## Resources

- Refer to `references/java-python-mapping.md` for detailed type conversions.
- Refer to `references/fastapi-best-practices.md` for structural guidelines.