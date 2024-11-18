import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_telemetry():
    resource = Resource(
        attributes={
            "service.name": "locaLLM",
            "service.version": "1.1.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
        }
    )

    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer = trace.get_tracer("locaLLMTracer")
    span_processor = BatchSpanProcessor(
        JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", 6831)),
        )
    )
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Instrumentations
    LoggingInstrumentor().instrument(set_logging_format=True)
    RequestsInstrumentor().instrument()