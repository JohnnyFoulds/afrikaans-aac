# Logging Standard

## Purpose

This document defines the structured logging requirements for all AIBooster+ GenAI services and libraries. It covers log levels, message formatting, logger naming, and the relationship between logs and OpenTelemetry traces. For tracing, metrics, and full observability instrumentation, see [telemetry-standard.md](telemetry-standard.md).

---

## 1. Log Levels

Use the standard Python `logging` levels as follows:

| Level | When to Use |
| --- | --- |
| `ERROR` | Unexpected failures, unhandled exceptions, I/O failures, degraded-mode events |
| `WARNING` | Expected-but-notable conditions: retries, rate limits, fallback paths, approaching limits |
| `INFO` | State transitions, lifecycle events, completion of significant operations |
| `DEBUG` | Internal state, intermediate values, verbose diagnostic information |

### Rules

- `ERROR` must always be used at exception catch sites. See [error-handling.md](../coding/error-handling.md) for the full error logging standard.
- Do not use `INFO` for high-frequency per-item events inside loops — use `DEBUG`.
- Do not use `WARNING` for errors that require action — use `ERROR`.
- `CRITICAL` is reserved for conditions that require immediate human intervention (e.g. unrecoverable startup failure). Do not use it for ordinary errors.

---

## 2. Logger Naming

### 2.1 Services and Routers

Use `logging.getLogger(__name__)` at module level. This produces a logger hierarchy that mirrors the package structure, making it easy to control log levels per module.

```python
import logging

logger = logging.getLogger(__name__)
```

### 2.2 Library Code with Injected Loggers

Library code that accepts a `ContextLogger` (e.g. via the `MLContext` protocol) must use the injected logger, not a module-level logger. This allows the caller to control the logging destination and correlation context.

```python
# Good — use the injected logger
ctx.logger.info("Session created session_id=%s", session_id)

# Bad — bypasses the injected context logger
logger = logging.getLogger(__name__)
logger.info("Session created")
```

---

## 3. Message Format

### 3.1 Include Resource Identifiers

Every log message must include the relevant resource identifiers (session ID, project ID, user ID, run ID) so that log records can be correlated across a request lifecycle.

```python
# Good
logger.info("Session paused session_id=%s user_id=%s", session_id, user_id)

# Bad — no identifiers; impossible to correlate in production
logger.info("Session paused")
```

### 3.2 Use `extra={}` for Structured Fields

When log records are shipped to a structured log backend, pass identifiers as `extra` fields rather than embedding them in the message string. This makes them queryable as structured fields.

```python
logger.info(
    "Session paused",
    extra={"session_id": session_id, "user_id": user_id},
)
```

Both styles are acceptable; prefer `extra={}` for services that ship logs to a backend.

### 3.3 `exc_info=True` at ERROR Level

Every `logger.error()` call at an exception catch site must include `exc_info=True` to ensure the stack trace is captured. See [error-handling.md §5.1](../coding/error-handling.md) for catch-site examples.

### 3.4 Use `%s` Formatting, Not f-strings

Use `%`-style lazy formatting in log calls. The logging module only performs string interpolation if the message is actually going to be emitted — f-strings evaluate immediately regardless of level.

```python
# Good — lazy evaluation
logger.debug("Processing item %d of %d: type=%s", i, total, item_type)

# Bad — always evaluates the f-string even if DEBUG is disabled
logger.debug(f"Processing item {i} of {total}: type={item_type}")
```

---

## 4. What to Log vs. What to Attribute

When OpenTelemetry tracing is active, do not duplicate information between log messages and span attributes. Use this split:

| Data type | Where it belongs |
| --- | --- |
| Counts, IDs, durations, status codes | Span attributes — structured and queryable |
| Narrative context, warning conditions, human-readable descriptions | Log messages |
| Exceptions and stack traces | `logger.error(..., exc_info=True)` + `span.record_exception(e)` |

If you set `span.set_attribute("session_id", session_id)`, you do not also need `logger.debug("session_id=%s", session_id)` unless the log message adds context the attribute does not carry.

---

## 5. Trace Correlation (OTel Log Bridge)

When OpenTelemetry is configured, add the OTel logging bridge so that every log record is automatically correlated with the active trace via `trace_id` and `span_id`. This links log lines to the specific execution that produced them.

```python
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogRecordExporter

def _setup_log_bridge(resource) -> None:
    """Wire the OTel logging bridge so existing log calls gain trace correlation."""
    log_provider = LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        BatchLogRecordProcessor(ConsoleLogRecordExporter())
    )
    set_logger_provider(log_provider)

    handler = LoggingHandler(level=logging.DEBUG, logger_provider=log_provider)
    logging.getLogger().addHandler(handler)
```

Call `_setup_log_bridge(resource)` alongside `_setup_tracing()` during service initialisation. Existing `logger.info(...)`, `logger.warning(...)`, and `logger.error(...)` calls require no changes — they automatically gain `trace_id` and `span_id` after the bridge is installed.

For details on setting up the `resource` object, see [telemetry-standard.md](telemetry-standard.md).

---

## 6. Log Configuration

### 6.1 Services (FastAPI)

Configure logging via `logging.config.dictConfig` in `main.py`. Set the root logger level to `WARNING` and configure the application logger at `INFO`:

```python
import logging.config

logging.config.dictConfig({
    "version": 1,
    "incremental": False,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {"level": "WARNING", "handlers": ["console"]},
    "loggers": {
        "app": {"level": "INFO", "propagate": True},
    },
})
```

### 6.2 Libraries

Libraries must never configure logging (no `basicConfig`, no handler attachment, no level setting). Configuration is always the caller's responsibility. A library that configures logging will interfere with the host application's log setup.

---

## References

- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Python logging — logging.config](https://docs.python.org/3/library/logging.config.html)
- [Python logging.Logger.error](https://docs.python.org/3/library/logging.html#logging.Logger.error)
- [OpenTelemetry — Logs Bridge API](https://opentelemetry.io/docs/concepts/signals/logs/)
- [OpenTelemetry Python — Logs](https://opentelemetry.io/docs/languages/python/instrumentation/#logs)
- [12 Factor App — Logs](https://12factor.net/logs)
