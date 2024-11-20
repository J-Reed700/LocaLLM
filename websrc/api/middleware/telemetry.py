import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

def setup_telemetry(app):
    resource = Resource(
        attributes={
            "service.name": "locaLLM",
            "service.version": "1.1.0",
            "environment": os.getenv("ENVIRONMENT", "production"),
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317')}"
    )

    provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    FastAPIInstrumentor.instrument_app(app)

    # Instrumentations
    LoggingInstrumentor().instrument(set_logging_format=True)
    RequestsInstrumentor().instrument()