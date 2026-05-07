# Observability — Enterprise Standard

**Applies to:** All Python services deployed to production.
**Stack:** OpenTelemetry (traces + metrics) + structlog (logs). The three pillars.

---

## SECTION 1 — OPENTELEMETRY SETUP

```bash
pip install opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-sqlalchemy \
    opentelemetry-instrumentation-httpx \
    opentelemetry-exporter-otlp
```

```python
# app/core/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION


def configure_telemetry(service_name: str, service_version: str) -> None:
    """Initialize OpenTelemetry. Call once at startup."""
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })

    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=30000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
```

---

## SECTION 2 — FASTAPI INTEGRATION

```python
# app/main.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_telemetry(settings.app_name, settings.app_version)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    HTTPXClientInstrumentor().instrument()
    yield
```

---

## SECTION 3 — CUSTOM SPANS

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


async def process_order(order_id: int) -> Order:
    with tracer.start_as_current_span("process_order", attributes={"order.id": order_id}) as span:
        order = await order_repo.get(order_id)
        if not order:
            span.set_status(trace.StatusCode.ERROR, "Order not found")
            raise NotFoundError("Order", order_id)

        span.add_event("payment_started")
        await payment_service.charge(order)
        span.add_event("payment_completed")

        return order
```

---

## SECTION 4 — METRICS PATTERNS

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)

# Counter — things that only go up
request_counter = meter.create_counter(
    "http.requests.total",
    description="Total HTTP requests",
)

# Histogram — measure distributions (latency, sizes)
request_duration = meter.create_histogram(
    "http.request.duration_ms",
    description="Request duration in milliseconds",
    unit="ms",
)

# UpDownCounter — things that go up and down (active connections, queue depth)
active_connections = meter.create_up_down_counter(
    "db.connections.active",
    description="Active database connections",
)
```

### Middleware for automatic HTTP metrics:

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000

        request_counter.add(1, {"method": request.method, "path": request.url.path, "status": response.status_code})
        request_duration.record(duration, {"method": request.method, "path": request.url.path})

        return response
```

---

## SECTION 5 — STRUCTURED LOGS + TRACE CORRELATION

```python
# Inject trace_id into every log line
import structlog
from opentelemetry import trace


def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


structlog.configure(
    processors=[
        add_trace_context,
        structlog.processors.JSONRenderer(),
    ]
)
```

---

## SECTION 6 — KEY METRICS TO TRACK (RED + USE)

### RED Method (request-driven services):

| Metric | What | Alert when |
|--------|------|------------|
| **R**ate | Requests per second | Sudden drop (service down) or spike (DDoS) |
| **E**rrors | Error rate (5xx / total) | > 1% sustained |
| **D**uration | p50, p95, p99 latency | p99 > SLO threshold |

### USE Method (resources):

| Metric | What | Alert when |
|--------|------|------------|
| **U**tilization | CPU/memory/disk % | > 80% sustained |
| **S**aturation | Queue depth, thread pool exhaustion | Growing unbounded |
| **E**rrors | Connection failures, OOM kills | Any occurrence |

---

## SECTION 7 — RULES

- Every service MUST export traces and metrics to an OTLP collector.
- Trace IDs MUST appear in log lines for correlation.
- Custom spans for any operation > 100ms or crossing a service boundary.
- Never log PII in span attributes (user emails, passwords, tokens).
- Use semantic conventions for attribute names (`http.method`, `db.system`, `rpc.service`).
- Set up alerts for SLO breaches, not just threshold crossings.
- Dashboard per service: request rate, error rate, p95 latency, resource utilization.
