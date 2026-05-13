import os, logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)
OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
SERVICE_NAME  = os.environ.get("OTEL_SERVICE_NAME", "ltm-chat-service")
_tracer = None

def setup_otel():
    global _tracer
    if _tracer is not None:
        return _tracer
    resource = Resource.create({"service.name": SERVICE_NAME, "service.version": "1.0.0"})
    provider = TracerProvider(resource=resource)
    otlp_url = OTEL_ENDPOINT.rstrip("/") + "/v1/traces"
    try:
        otlp_exp = OTLPSpanExporter(endpoint=otlp_url, headers={})
        provider.add_span_processor(BatchSpanProcessor(otlp_exp))
        logger.info("[OTEL] OTLP exporter configured -> %s", otlp_url)
    except Exception as e:
        logger.warning("[OTEL] OTLP exporter init failed: %s", e)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(SERVICE_NAME)
    logger.info("[OTEL] Tracer ready service=%s endpoint=%s", SERVICE_NAME, otlp_url)
    return _tracer

def get_tracer():
    global _tracer
    return _tracer if _tracer else setup_otel()

def span_to_ids(span):
    ctx = span.get_span_context()
    return {
        "trace_id": format(ctx.trace_id, "032x") if ctx and ctx.trace_id else "",
        "span_id":  format(ctx.span_id, "016x")  if ctx and ctx.span_id  else "",
    }
