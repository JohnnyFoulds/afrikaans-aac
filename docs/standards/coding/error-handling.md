# Error Handling Standard

## Purpose

This document defines how errors should be raised, propagated, caught, logged, and surfaced to callers across all AIBooster+ GenAI services and libraries. It is based on an audit of `aib-genai-ml-context`, `aib-genai-agent-core-session-manager`, and `aib-genai-agent-core-interface-api`.

---

## 1. Exception Hierarchy

### 1.1 Domain Exceptions

Every library and service **must** define a base exception class that is exported as part of its public API. All domain-specific exceptions must inherit from it.

```python
class AgentError(Exception):
    """Base class for all errors raised by this package."""
```

Domain exceptions must be specific and named after the condition they represent:

```python
class SessionNotFoundError(AgentError): ...
class SessionClosedError(AgentError): ...
class ProjectNotFoundError(AgentError): ...
class UnauthorizedError(AgentError): ...
```

**Do not** raise raw `ValueError`, `RuntimeError`, or `KeyError` from a library's public interface. Use domain exceptions for conditions callers are expected to handle. Reserve `ValueError` for true argument validation errors on a function's own parameters (e.g. an empty string where one is required), where no more specific type exists.

### 1.2 Flat vs Deep Hierarchies

Keep hierarchies shallow. A single base class plus one level of specific exceptions is sufficient for most libraries. Do not create exception classes just to have them — only define a type if callers need to catch it distinctly from others.

---

## 2. Raising Errors

### 2.1 Be Explicit and Informative

Every raised exception must include a message that identifies:
- **What** failed
- **Which value or resource** was involved (include IDs, keys, names)
- **Why** it failed (if not obvious from the exception type)

```python
# Bad — caller cannot identify which session failed
raise SessionNotFoundError("Session not found")

# Good
raise SessionNotFoundError(f"Session '{session_id}' not found for user '{user_id}'")
```

Never rely on implicit raises from dict access (`self._data[key]`) or attribute access in a library's public interface. Raise explicitly.

### 2.2 Exception Chaining

When wrapping a lower-level exception in a higher-level one, always use `raise ... from exc` to preserve the original traceback:

```python
try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    raise CorruptSessionError(f"Invalid JSON in session artifact '{artifact}'") from exc
```

Never `raise ... from None` unless you are intentionally suppressing the original cause and have a documented reason.

### 2.3 Layer Boundaries

**Services must not raise HTTP-layer exceptions.** Service classes must raise domain exceptions. Routers are responsible for converting domain exceptions to `HTTPException`.

```python
# Bad — service is coupled to FastAPI
class SessionService:
    def get_session(self, session_id: str) -> Session:
        if not found:
            raise HTTPException(status_code=404, detail="Session not found")

# Good
class SessionService:
    def get_session(self, session_id: str) -> Session:
        if not found:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

# Router converts
@router.get("/sessions/{session_id}")
def get_session(session_id: str, service: SessionService = Depends()):
    try:
        return service.get_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error_code": ErrorCode.SESSION_NOT_FOUND, "message": str(exc)},
        )
```

---

## 3. Catching Errors

### 3.1 Catch the Most Specific Exception

Always catch the most specific exception type available. `except Exception` is the maximum permissible catch scope — never use `except BaseException`, as it swallows `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`, which must propagate freely (this matters especially in async and streaming code).

Only use `except Exception` at top-level handlers (e.g. a FastAPI exception handler or request lifecycle guard), and always log the traceback.

```python
# Bad — swallows everything including signals
try:
    result = do_thing()
except BaseException:
    pass

# Bad — silently swallows (the problem is pass, not Exception itself)
try:
    result = do_thing()
except Exception:
    pass

# Good
try:
    result = do_thing()
except (ValueError, RuntimeError) as exc:
    logger.error("do_thing failed", exc_info=True)
    raise
```

### 3.2 Never Swallow Errors Silently

Do not catch exceptions and do nothing. The minimum acceptable action is `logger.error(..., exc_info=True)`. If a subsystem failure is intentionally non-critical (e.g. usage tracking, background sync), this must be:
1. Explicitly documented in a comment at the catch site.
2. Logged at `error` level with `exc_info=True`.

```python
try:
    await usage_service.update(result)
except Exception:
    # Non-critical: usage tracking failure must not fail the user's request.
    logger.error("Failed to update usage tracking", exc_info=True)
```

### 3.3 Consistent Read Error Policy

Within a single data store or storage abstraction, read errors and not-found conditions must be handled consistently. Do not return `None` for failures in one method and re-raise in another for the same class of error.

---

## 4. HTTP Error Responses

### 4.1 Status Code Mapping

All services must follow this mapping from domain conditions to HTTP status codes:

| Condition | Status Code |
| --- | --- |
| Resource not found | 404 |
| Caller not authorized | 403 |
| Invalid input / bad request | 400 |
| Resource already exists (conflict) | 409 |
| Payload too large | 413 |
| Semantic validation failure | 422 |
| Unhandled internal error | 500 |

### 4.2 Response Body Shape

All HTTP error responses must use a shape inspired by [RFC 7807 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc7807):

```json
{
  "error_code": "session_not_found",
  "message": "Session 'abc-123' not found for user 'user-456'",
  "detail": {}
}
```

| Field | Required | Description |
| --- | --- | --- |
| `error_code` | Yes | Snake-case machine-readable identifier (see §4.3). Corresponds to RFC 7807 `type`. |
| `message` | Yes | Human-readable description suitable for logging or display. Corresponds to RFC 7807 `detail`. |
| `detail` | No | Optional structured context (e.g. resource IDs, constraint values). Extension beyond RFC 7807. |

**Deviation from RFC 7807:** We use `error_code` (a short token) rather than the RFC's `type` URI, and `message` rather than `title`/`detail`, to keep the shape simpler for internal APIs. If a service exposes a public or partner-facing API, full RFC 7807 compliance should be considered.

Register a global FastAPI exception handler to convert domain exceptions to this shape automatically, rather than constructing responses manually in each router.

### 4.3 Error Codes

Error codes must be snake-case strings, globally unique within a service, and defined as constants or an enum — not scattered as string literals across routers.

```python
class ErrorCode(str, Enum):
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_CLOSED = "session_closed"
    PROJECT_NOT_FOUND = "project_not_found"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED = "unauthorized"
```

### 4.4 Streaming (SSE) Errors

For streaming endpoints, two distinct error channels exist:

- **Pre-stream errors** (e.g. session not found, unauthorized): return a standard HTTP error response before the stream begins.
- **Mid-stream errors** (e.g. model error, downstream timeout): emit a structured SSE error event.

SSE error events must use this shape:

```json
{
  "type": "error",
  "error_code": "rate_limit_exceeded",
  "message": "Daily token limit exceeded",
  "detail": {}
}
```

The contract for which errors appear in which channel must be documented on the endpoint.

---

## 5. Error Logging

Log levels, logger naming, message format, and `exc_info` requirements are defined in [logging-standard.md](../logging/logging-standard.md). The rules below are the error-handling-specific requirements that apply at exception catch sites.

### 5.1 Always Include `exc_info=True` at ERROR Level

Every `logger.error()` call at an exception catch site must include `exc_info=True` to ensure the stack trace appears in the log output.

```python
# Bad — exc_info omitted; no stack trace in the log
try:
    sync()
except RuntimeError:
    logger.error("S3 sync failed")

# Good
try:
    sync()
except RuntimeError:
    logger.error("S3 sync failed for session '%s'", session_id, exc_info=True)
```

### 5.2 Include Identifiers as Structured Fields

Log messages must include relevant resource identifiers (session ID, project ID, user ID) so log records can be correlated. Prefer structured key-value pairs in the message or as `extra={}` fields over free-text embedding.

```python
logger.error(
    "Failed to load session",
    extra={"session_id": session_id, "user_id": user_id},
    exc_info=True,
)
```

---

## 6. Retry and Resilience

### 6.1 Retry Policy

Retry logic must use exponential backoff with jitter. Retry only on transient failures (I/O timeouts, network errors, throttling). Do not retry on validation errors or authorization failures.

Recommended defaults for external I/O (e.g. S3, AWS services):
- Max attempts: 3
- Initial delay: 2 s
- Backoff multiplier: 2×

### 6.2 Retry Failures Must Not Be Silently Swallowed

If all retry attempts are exhausted, the final exception must either be re-raised or produce an observable side-effect — at minimum an `ERROR` log with `exc_info=True`. Silent exhaustion is prohibited.

---

## 7. Documentation

### 7.1 Docstrings

Public functions and methods must document the exceptions they raise using `:raises <ExceptionType>: <condition>` in the docstring. This applies to all library code; it is optional (but encouraged) for internal/private functions.

```python
def get_session(self, session_id: str) -> Session:
    """
    Retrieve a session by ID.

    :param session_id:            The session identifier.
    :returns:                     The Session object.
    :raises SessionNotFoundError: If no session with the given ID exists.
    :raises SessionClosedError:   If the session has been terminated.
    """
```

### 7.2 Non-Critical Catch Sites

Any `except` block that intentionally swallows or demotes an error must include a comment explaining why the failure is safe to ignore, and must still log at `error` level as specified in §3.2.

---

## References

### RFCs and Standards

- [RFC 7807 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc7807) — IETF standard for HTTP error response bodies. Our response shape is inspired by this.
- [RFC 9457 — Problem Details for HTTP APIs (updated)](https://www.rfc-editor.org/rfc/rfc9457) — Supersedes RFC 7807. Adds `errors` array for multiple problems and clarifies extension fields.
- [PEP 3134 — Exception Chaining and Embedded Tracebacks](https://peps.python.org/pep-3134/) — Defines `raise X from Y` semantics.
- [PEP 352 — Required Superclass for Exceptions](https://peps.python.org/pep-0352/) — Establishes `BaseException` / `Exception` hierarchy and why user-defined exceptions should inherit from `Exception`.
- [PEP 20 — The Zen of Python](https://peps.python.org/pep-0020/) — "Errors should never pass silently. Unless explicitly silenced."

### Python Documentation

- [Python Built-in Exceptions](https://docs.python.org/3/library/exceptions.html) — Canonical hierarchy of built-in exception types.
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html) — Covers `exc_info`, logger naming, and log levels.
- [Python logging.Logger.error](https://docs.python.org/3/library/logging.html#logging.Logger.error) — Documents the `exc_info` parameter.

### Industry Guidance

- [Google API Design Guide — Errors](https://cloud.google.com/apis/design/errors) — Google's conventions for error codes, status mapping, and error propagation in APIs.
- [AWS Architecture Blog — Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) — Rationale and implementation for retry with jitter.
- [FastAPI — Exception Handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/) — FastAPI's `HTTPException`, custom exception handlers, and `RequestValidationError`.
- [OWASP — Error Handling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html) — Security considerations for error messages and exception handling.

---

## Summary Checklist

- [ ] Package defines a base exception class and exports it
- [ ] Domain exceptions are specific, named, and inherit from the base
- [ ] No `HTTPException` raised from service layer classes
- [ ] All raises include a message with relevant identifiers
- [ ] Exception chaining uses `raise ... from exc`
- [ ] All `logger.error()` calls at catch sites include `exc_info=True`
- [ ] HTTP error responses use the standard `{error_code, message, detail}` shape
- [ ] Error codes are defined as constants, not scattered string literals
- [ ] SSE error events follow the documented shape
- [ ] Retry logic uses exponential backoff and does not swallow final failures
- [ ] Public API docstrings document raised exceptions
