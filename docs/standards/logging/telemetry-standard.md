# Telemetry Standard

## Purpose

This document defines the OpenTelemetry (OTel) instrumentation standard for all AIBooster+ GenAI services and pipelines. It covers distributed tracing, metrics, the OTel data model, semantic conventions, and instrumentation design rules. For structured logging with Python's `logging` module, see [logging-standard.md](logging-standard.md).

---

## 1. The Four Observability Signals

OTel defines four signals. Each answers a different question:

| Signal | Answers | When to use |
| --- | --- | --- |
| **Traces** | What happened in this specific execution? Where did time go? | Always — the primary diagnostic tool for any non-trivial operation |
| **Metrics** | How much, how often, how slow — across many executions? | Only when there is a concrete need to aggregate data over time |
| **Logs** | What discrete events occurred, and when? | Via the OTel bridge; existing `logging` calls require no changes |
| **Baggage** | Cross-service key-value context propagation | When context must flow across service boundaries without being a span attribute |

**Profilers** (`py-spy`, `scalene`, `cProfile`) are not OTel signals but are complementary — use them when a trace identifies a slow span but doesn't reveal which line inside it is the cause.

### Signal selection rules

- Start with traces. Do not add metrics until traces have confirmed the need.
- Do not replace structured span attributes with unstructured log messages.
- Use span events for timestamped annotations within a span (a retry, a cache miss). Use span attributes for stable, queryable metadata. Use logs for narrative context.

---

## 2. Core Concepts

### 2.1 Data Model

```text
Trace
└── Root span  (e.g. "handle_query")
    ├── Child span  (e.g. "load_session")
    └── Child span  (e.g. "invoke_model")
        ├── Child span  ("token_count")
        └── Child span  ("stream_response")
```

| Concept | Description |
| --- | --- |
| **Trace** | One complete execution from entry to exit. All spans share a `trace_id`. The unit of investigation. |
| **Span** | One named operation: start timestamp, end timestamp, status, and key-value attributes. The unit of measurement. |
| **Span Context** | Immutable object on every span: `trace_id`, `span_id`, `trace_flags`, `trace_state`. Serialised for cross-service propagation. |
| **Attributes** | Structured key-value metadata on a span. Keys: non-null strings. Values: strings, booleans, floats, integers, or arrays. |
| **Span Events** | Timestamped annotations on a span. Use when *when* matters (e.g. a retry mid-span). |
| **Span Links** | Associate a span causally with a span in a different trace. Use for async/queue-driven pipelines. |
| **Resource** | Metadata about the service itself, set once at provider init (`service.name`, `service.version`, `deployment.environment`). |

### 2.2 Provider → Processor → Exporter Chain

```text
Instrumentation code
    → TracerProvider
        → SpanProcessor
            → SpanExporter
```

| Component | Notes |
| --- | --- |
| `TracerProvider` | One per process. Created once in `_setup_tracing()`, registered globally with `trace.set_tracer_provider()`. |
| `SimpleSpanProcessor` | Synchronous — sends each span immediately. Use **only** with `ConsoleSpanExporter` in development. Blocks the calling thread. |
| `BatchSpanProcessor` | Asynchronous — buffers and sends on a background thread. **Required** for all OTLP export. |
| `ConsoleSpanExporter` | Writes span JSON to stdout. Opt-in for CLI tools; always-on for services during development. |
| `OTLPSpanExporter` (gRPC) | Ships spans to any OTLP-compatible backend (Jaeger, Grafana Tempo, Honeycomb, Datadog). Activated by `OTEL_EXPORTER_OTLP_ENDPOINT`. |

### 2.3 Span Lifecycle

```python
with tracer.start_as_current_span("operation_name") as span:
    span.set_attribute("input.count", len(items))
    result = do_work(items)
    span.set_attribute("output.count", len(result))
```

The span starts when the `with` block is entered and ends when it exits. If an exception propagates out, the span status is automatically set to `ERROR` and the exception recorded. Set input attributes before the work and output attributes after — data is then present even on error.

### 2.4 Span Status and Error Recording

```python
from opentelemetry.trace import Status, StatusCode

with tracer.start_as_current_span("call_model") as span:
    try:
        result = model.invoke(prompt)
    except ModelError as exc:
        span.record_exception(exc)
        span.set_status(Status(StatusCode.ERROR, description=str(exc)))
        raise
```

| Status | Meaning |
| --- | --- |
| `Unset` (default) | Completed without error — implies success |
| `Error` | An error occurred |
| `Ok` | Explicitly declared error-free (rarely needed) |

Never swallow an exception inside a span without calling `span.record_exception()`. A span ending with `Unset` after catching an exception is misleading.

### 2.5 Span Kind

Set span kind for any non-internal operation:

| Kind | Use for |
| --- | --- |
| `Internal` | Operations that do not cross a process boundary (default) |
| `Client` | Outgoing synchronous remote calls (HTTP, DB query, model API) |
| `Server` | Incoming synchronous remote calls (HTTP handler, RPC) |
| `Producer` | Creates a job for async processing (enqueue) |
| `Consumer` | Processes a job from a producer (dequeue) |

```python
from opentelemetry.trace import SpanKind

with tracer.start_as_current_span("bedrock_invoke", kind=SpanKind.CLIENT) as span:
    span.set_attribute("gen_ai.system", "aws_bedrock")
    span.set_attribute("gen_ai.request.model", model_id)
```

---

## 3. Standard Setup Pattern

Every service must follow this pattern. Adjust `service.name`, `service.version`, and `deployment.environment.name` per service.

### 3.1 Dependencies

Add to `requirements.txt`:

```text
opentelemetry-sdk>=1.40.0
opentelemetry-exporter-otlp-proto-grpc>=1.40.0
opentelemetry-semantic-conventions>=0.41b0
```

### 3.2 `_setup_tracing()`

```python
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)


def _setup_tracing(console_trace: bool = False) -> trace.Tracer:
    """
    Configure OpenTelemetry tracing with optional console output and OTLP export.

    Console output is opt-in for CLI tools (``OTEL_TRACE_CONSOLE=1``).
    OTLP export is activated by setting ``OTEL_EXPORTER_OTLP_ENDPOINT``.

    :param console_trace: When ``True``, print span JSON to stdout unconditionally.
    :returns:             A tracer instance for this module.
    """
    resource = Resource.create({
        "service.name": "aib-genai-<service-name>",
        "service.version": "1.0.0",
        "deployment.environment.name": os.getenv("DEPLOYMENT_ENV", "development"),
    })
    provider = TracerProvider(resource=resource)

    if console_trace or os.environ.get("OTEL_TRACE_CONSOLE") == "1":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )

    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)
```

Call `_setup_tracing()` once at service startup. Pass the returned tracer explicitly into functions that need it — do not call `trace.get_tracer()` outside of `_setup_tracing()`.

### 3.3 Environment Variables

| Variable | Effect |
| --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Activates OTLP export (e.g. `http://localhost:4317`) |
| `OTEL_TRACE_CONSOLE` | Set to `1` to enable console span output |
| `OTEL_SERVICE_NAME` | Overrides `service.name` set in Resource |
| `OTEL_RESOURCE_ATTRIBUTES` | Comma-separated `key=value` resource attributes |
| `OTEL_PROPAGATORS` | Propagation format: `tracecontext` (default), `b3`, `jaeger` |
| `OTEL_TRACES_SAMPLER` | Sampler: `always_on` (default), `parentbased_traceidratio` |
| `OTEL_TRACES_SAMPLER_ARG` | Sampling rate when using `parentbased_traceidratio` (e.g. `0.1`) |

---

## 4. Semantic Conventions

Use OTel Semantic Conventions wherever applicable. Do not invent custom attribute names for concepts that already have a standard.

### 4.1 Key Namespaces

| Namespace | Domain |
| --- | --- |
| `service.*` | Service identity |
| `http.*` | HTTP client/server spans |
| `db.*` | Database calls (SQL, Redis, etc.) |
| `messaging.*` | Kafka, SQS, Pub/Sub |
| `gen_ai.*` | LLM / generative AI operations |
| `error.*` | Error classification |

### 4.2 Custom Attribute Naming

When no standard attribute exists, use `namespace.attribute` dot-notation in lowercase `snake_case`:

```python
# Good
span.set_attribute("session.message_count", count)
span.set_attribute("model.input_tokens", prompt_tokens)
span.set_attribute("model.output_tokens", completion_tokens)

# Bad — flat names, not queryable across services
span.set_attribute("count", count)
span.set_attribute("tokens", prompt_tokens)
```

Use native types: `int` for counts, `float` for durations in seconds, `bool` for flags, `str` for identifiers. Never stringify numbers.

---

## 5. Context Propagation

OTel automatically tracks the active span in context. Child spans created with `start_as_current_span()` are automatically parented to the active span — no manual parent tracking required.

For distributed tracing across HTTP services, inject the trace context into outgoing headers and extract it on the receiving side:

```python
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Outgoing request — inject context
with tracer.start_as_current_span("call_downstream", kind=SpanKind.CLIENT):
    headers = {}
    TraceContextTextMapPropagator().inject(headers)
    requests.post("http://downstream-service/", headers=headers)

# Incoming request — extract context
carrier = {"traceparent": request.headers.get("traceparent", "")}
ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
with tracer.start_as_current_span("handle_request", context=ctx, kind=SpanKind.SERVER):
    pass
```

The default propagation format is **W3C TraceContext** (`traceparent` header).

---

## 6. Metrics

Add metrics only when there is a concrete need to aggregate data across many executions. Do not add metrics to operations that are adequately represented by traces.

### 6.1 Instrument Types

| Instrument | Use for |
| --- | --- |
| `Counter` | Values that only increase (items processed, requests served) |
| `UpDownCounter` | Values that can increase or decrease (active sessions, queue depth) |
| `Gauge` | Point-in-time snapshot (current memory usage) |
| `Histogram` | Latency and size distributions (model response time, token counts) |

### 6.2 MeterProvider Setup

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)

reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)
```

### 6.3 Example

```python
query_counter = meter.create_counter(
    "agent.queries_total",
    unit="1",
    description="Total number of agent queries processed",
)

token_histogram = meter.create_histogram(
    "agent.tokens",
    unit="tokens",
    description="Token counts per model invocation",
)

# In request handler:
query_counter.add(1, {"agent.type": agent_type, "query.status": "success"})
token_histogram.record(usage.total_tokens, {"model.id": model_id})
```

---

## 7. Instrumentation Design Rules

### Rule 1: Instrument at the operation boundary

A span should correspond to one logical operation with a clear input, output, and measurable duration. The name should describe *what*, not *how*.

```python
# Good — one span per logical phase
with tracer.start_as_current_span("load_session") as span:
    span.set_attribute("session.id", session_id)
    session = await session_manager.resume(ctx)
    span.set_attribute("session.message_count", session.message_count)

# Bad — spans for internal implementation details
with tracer.start_as_current_span("check_if_session_id_is_not_none"):
    ...
```

### Rule 2: Every span must be self-describing

A span with no attributes forces correlation with log lines or source code. Minimum attributes by span type:

| Span type | Required attributes |
| --- | --- |
| Root / entry-point | All input parameters, output summary |
| I/O operations | Resource identifier (URL, path), item count or byte count |
| Model invocations | `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` |
| External calls | Endpoint, response status |
| Failures | Exception type and message via `record_exception()` |

### Rule 3: `BatchSpanProcessor` for OTLP; `SimpleSpanProcessor` only for console

Using `SimpleSpanProcessor` with OTLP blocks the calling thread on every export. Always use `BatchSpanProcessor` for any backend export.

### Rule 4: `service.name` is mandatory

Without it, spans from multiple services are indistinguishable in a shared backend. Use lowercase kebab-case matching the service name (e.g. `aib-genai-interface-api`).

### Rule 5: The root span must carry full execution context

The root span must carry enough attributes to reconstruct what the execution was doing without reading any other spans — this is what you query when searching for "all failed requests with a given session."

### Rule 6: Never put sensitive data in span attributes

Span attributes are exported to backends and potentially shipped to third-party services. Never include:

- Authentication tokens, cookies, or API keys
- Personally identifiable information (PII)
- Full request or response bodies (use counts or byte lengths instead)

### Rule 7: Span granularity follows the diagnostic need

- One span per major phase → identifies which phase is slow
- One span per item in a loop → identifies whether slowness is uniform or concentrated
- No span per Python statement → that is profiler territory (`py-spy`, `scalene`, `cProfile`)

---

## 8. Sampling

For most AIBooster+ GenAI services, sample all traces (the default `always_on` sampler). Add sampling only when generating high volumes that create a measurable cost.

Head-based sampling via environment variable:

```bash
export OTEL_TRACES_SAMPLER=parentbased_traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1  # 10%
```

Tail-based sampling (always sample errors, sample by latency) requires the OTel Collector with the Tail Sampling Processor — only justified at significant scale.

---

## 9. Observability Checklist

A service has adequate telemetry when any failure or performance regression can be diagnosed from the trace output alone, without reading source code.

- [ ] `service.name` is set on the Resource
- [ ] Root span carries all input parameters and output summary
- [ ] Every major operation has a dedicated span with relevant attributes
- [ ] Error spans call `span.record_exception(exc)` and set `StatusCode.ERROR`
- [ ] `BatchSpanProcessor` is used for all OTLP export
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` is supported without code changes
- [ ] OTel log bridge is wired so log records carry `trace_id` and `span_id`
- [ ] Sensitive data (tokens, PII, secrets) is never in span attributes
- [ ] Span kinds are set for HTTP, DB, and model API calls
- [ ] Semantic convention attributes are used where applicable

---

## References

- [OpenTelemetry — What is OpenTelemetry?](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [OpenTelemetry Python — Instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [OpenTelemetry Python — Exporters](https://opentelemetry.io/docs/languages/python/exporters/)
- [OpenTelemetry Python — Propagation](https://opentelemetry.io/docs/languages/python/propagation/)
- [OpenTelemetry Concepts — Traces](https://opentelemetry.io/docs/concepts/signals/traces/)
- [OpenTelemetry Concepts — Metrics](https://opentelemetry.io/docs/concepts/signals/metrics/)
- [OpenTelemetry Concepts — Logs](https://opentelemetry.io/docs/concepts/signals/logs/)
- [OpenTelemetry Concepts — Sampling](https://opentelemetry.io/docs/concepts/sampling/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
