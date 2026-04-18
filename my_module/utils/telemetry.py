"""
OpenTelemetry instrumentation utilities for Odoo modules.

Consumes the global TracerProvider/MeterProvider — does NOT initialize its own.
The provider is expected to be set up externally (e.g. by a platform observability
module or opentelemetry-instrument auto-instrumentation before Odoo starts).

Gracefully degrades to no-ops if opentelemetry is not installed or no provider
has been configured — the Odoo module continues working normally.

Usage in models:
    from ..utils import telemetry as otel

    def my_method(self):
        with otel.start_span("my_module.my_method") as span:
            span.set_attribute("record.id", self.id)
            span.set_attribute("record.name", self.name)
            otel.record_event("my_event", {"type": "example"})
            ...
"""
import logging
import threading

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful import — module works fine without opentelemetry installed
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace, metrics
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False
    _logger.info(
        "opentelemetry-sdk not installed — telemetry disabled. "
        "Run: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
    )

# ---------------------------------------------------------------------------
# Lazy, thread-safe, idempotent initialization
# ---------------------------------------------------------------------------
_init_lock = threading.Lock()
_initialized = False
_tracer = None
_meter = None

# Business metric instruments — replace with your module's domain metrics
_event_counter = None


# ---------------------------------------------------------------------------
# No-op fallback span — same interface as an OTel span
# ---------------------------------------------------------------------------
class _NoOpSpan:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def set_attribute(self, key, value):
        pass

    def record_exception(self, exc, attributes=None):
        pass

    def set_status(self, status, description=None):
        pass

    def add_event(self, name, attributes=None):
        pass


def _init():
    """Initialize OTel instruments from the global provider. Thread-safe, idempotent."""
    global _initialized, _tracer, _meter, _event_counter

    if _initialized or not _OTEL_AVAILABLE:
        return

    with _init_lock:
        if _initialized:
            return  # double-checked locking

        # Uses the global provider set up by nakel_otel (or any OTel initializer).
        # If no provider is configured yet, OTel returns a no-op tracer/meter automatically.
        _tracer = trace.get_tracer(__name__)
        _meter = metrics.get_meter(__name__)

        # ----------------------------------------------------------------
        # Define your module's business metric instruments below.
        # Replace / extend these with domain-specific counters/histograms.
        # ----------------------------------------------------------------
        _event_counter = _meter.create_counter(
            name="my_module_events_total",
            description="Total events processed by my_module",
            unit="1",
        )

        _initialized = True
        _logger.info("OTel telemetry initialized for %s", __name__)


# ---------------------------------------------------------------------------
# Public helpers — safe to call even when OTel is not installed
# ---------------------------------------------------------------------------

def start_span(name: str):
    """
    Return a context manager that opens an OTel span (or a no-op).

    Usage::

        with otel.start_span("my_module.do_something") as span:
            span.set_attribute("record.id", self.id)
            ...
    """
    _init()
    if not _OTEL_AVAILABLE or _tracer is None:
        return _NoOpSpan()
    return _tracer.start_as_current_span(name)


def record_event(event_name: str, attributes: dict = None):
    """
    Increment the generic event counter.

    Replace this with domain-specific recording functions for your module,
    e.g. record_order_confirmed(), record_validation_skipped(), etc.
    """
    _init()
    if _event_counter:
        _event_counter.add(1, attributes or {})
