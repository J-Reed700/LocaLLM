import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from websrc.config.settings import settings

def setup_telemetry(app):
    resource = Resource(
        attributes={
            "service.name": settings.SERVICE_NAME,
            "service.version": settings.SERVICE_VERSION,
            "environment": settings.ENVIRONMENT,
            "telemetry.sdk.name": settings.TELEMETRY_SDK_NAME,
            "telemetry.sdk.language": settings.TELEMETRY_SDK_LANGUAGE,
            "telemetry.sdk.version": settings.TELEMETRY_SDK_VERSION,
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))

    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTLP_ENDPOINT,
            headers={
                "Content-Type": "application/x-protobuf"
            }
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    except Exception as e:
        print(f"Failed to initialize OTLP exporter: {e}")

    FastAPIInstrumentor.instrument_app(app)
    LoggingInstrumentor().instrument(set_logging_format=True)
    RequestsInstrumentor().instrument()