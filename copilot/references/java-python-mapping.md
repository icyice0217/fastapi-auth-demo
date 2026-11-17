

# JDK 17 → Python 3.12 Type and Syntax Mapping Reference

## 1. Primitive Data Types Mapping

| Java 17 Type | Python 3.12 Type | Notes |
| :--- | :--- | :--- |
| `byte` / `Byte` | `int` | Python has no separate byte type; range validation must be handled manually |
| `short` / `Short` | `int` | Directly mapped to native integer |
| `int` / `Integer` | `int` | Python 3 int is arbitrary precision, no overflow issues |
| `long` / `Long` | `int` | No extra declaration needed; Python natively supports large integers |
| `float` / `Float` | `float` | 64-bit double-precision floating point |
| `double` / `Double` | `float` | Python has no separate double type; float is double precision |
| `boolean` / `Boolean` | `bool` | Only `True`/`False` values; note capitalization |
| `char` / `Character` | `str` | String of length 1 |
| `String` | `str` | Python strings are Unicode encoded, default UTF-8 |
| `BigDecimal` | `decimal.Decimal` | High-precision decimal calculation; requires standard library import |
| `LocalDateTime` | `datetime.datetime` | Requires importing `datetime` standard library |
| `LocalDate` | `datetime.date` | Date type mapping |
| `LocalTime` | `datetime.time` | Time type mapping |

## 2. Collection Types Mapping

| Java 17 Collection | Python 3.12 Collection | Notes |
| :--- | :--- | :--- |
| `List<T>` | `list[T]` | Native generics in Python 3.9+; no need to import `typing.List` |
| `Set<T>` | `set[T]` | Native generic set; automatic deduplication |
| `Map<K,V>` | `dict[K, V]` | Native dictionary for key-value storage |
| `Queue<T>` | `collections.deque[T]` | Double-ended queue for efficient head/tail operations |
| `Optional<T>` | `T | None` | Union type syntax in Python 3.10+; no need to import `Optional` |
| `Stream<T>` | Generator expressions / List comprehensions | Replaces Java stream operations; more concise and efficient |

## 3. Object-Oriented Features Mapping

| Java 17 Feature | Python 3.12 Equivalent | Notes |
| :--- | :--- | :--- |
| Regular Class + Getters/Setters | Pydantic `BaseModel` | Automatically generates validation and serialization logic; replaces Lombok |
| Java 17 Record | `@dataclass` / Pydantic Model | Immutable data class; automatically generates `__eq__`/`__hash__` |
| Static Utility Class `XxxUtils` | Module-level functions | No need to create classes with only static methods; define functions directly in `.py` files |
| Interface | Abstract Base Class `abc.ABC` | Use `abc.ABCMeta` to enforce abstract method constraints |
| Enum | `enum.Enum` | Standard library enum; supports value mapping |
| Inheritance (`extends`) | Class inheritance `class Sub(Parent)` | Python supports multiple inheritance; prefer composition over complex inheritance |

## 4. Resource Loading Mapping

| Java 17 Resource Loading | Python 3.12 Recommended Implementation | Notes |
| :--- | :--- | :--- |
| `ClassLoader.getResourceAsStream()` | `importlib.resources.files()` | Compatible with packaged ZIP/EXE environments; do NOT use `__file__` path joining |
| `Files.readString(path)` | `pathlib.Path.read_text()` | Handles encoding automatically; no need to manually close file streams |
| Reading JSON from classpath | `resources.files().joinpath().read_text()` + `json.loads()` | Completely replaces Java resource stream reading logic |

## 5. Exception and Control Flow Mapping

| Java 17 Syntax | Python 3.12 Equivalent | Notes |
| :--- | :--- | :--- |
| `try-catch (Exception e)` | `try-except Exception as e` | Python exception handling is flexible; avoid bare `except:` |
| Java 17 Pattern Matching switch | `match-case` | Native structural pattern matching in Python 3.10+ |
| `for (T item : list)` | `for item in list:` | Direct iteration over iterable objects |
| `if (obj == null)` | `if obj is None:` | Strict null check; do NOT use `if not obj` which may misinterpret empty strings/0 |

