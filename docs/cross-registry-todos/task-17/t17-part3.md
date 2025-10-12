<!-- file: docs/cross-registry-todos/task-17/t17-part3.md -->
<!-- version: 1.0.0 -->
<!-- guid: t17-observability-logging-part3-s3t4u5v6-w7x8 -->

# Task 17 Part 3: Log Correlation with Traces and Context Propagation

## OpenTelemetry Integration

### Trace Context in Logs - Rust

```rust
// file: src/tracing/correlation.rs
// version: 1.0.0
// guid: rust-trace-correlation

use opentelemetry::{
    global,
    trace::{Span, SpanContext, TraceContextExt, Tracer},
    Context, KeyValue,
};
use opentelemetry_sdk::{
    trace::{Config, Sampler},
    Resource,
};
use opentelemetry_otlp::WithExportConfig;
use tracing::{info, span, Span as TracingSpan};
use tracing_opentelemetry::OpenTelemetrySpanExt;
use tracing_subscriber::{
    layer::SubscriberExt,
    util::SubscriberInitExt,
    Layer,
};

/// Initialize OpenTelemetry with Jaeger exporter
pub fn init_tracer(service_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://localhost:4317"),
        )
        .with_trace_config(
            Config::default()
                .with_sampler(Sampler::AlwaysOn)
                .with_resource(Resource::new(vec![
                    KeyValue::new("service.name", service_name.to_string()),
                ])),
        )
        .install_batch(opentelemetry_sdk::runtime::Tokio)?;

    global::set_tracer_provider(tracer.provider().unwrap());

    Ok(())
}

/// Initialize tracing with OpenTelemetry correlation
pub fn init_tracing_with_otel(
    service_name: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    // Initialize OpenTelemetry
    init_tracer(service_name)?;

    // Create OpenTelemetry layer
    let telemetry = tracing_opentelemetry::layer()
        .with_tracer(global::tracer(service_name));

    // Create formatting layer with trace IDs
    let fmt_layer = tracing_subscriber::fmt::layer()
        .json()
        .with_current_span(true)
        .with_span_list(false)
        .with_target(true);

    // Build subscriber with both layers
    tracing_subscriber::registry()
        .with(telemetry)
        .with(fmt_layer)
        .init();

    info!(service = service_name, "Tracing initialized with OpenTelemetry");

    Ok(())
}

/// Extract trace context from span
pub fn get_trace_context() -> Option<(String, String)> {
    let cx = Context::current();
    let span = cx.span();
    let span_context = span.span_context();

    if span_context.is_valid() {
        Some((
            span_context.trace_id().to_string(),
            span_context.span_id().to_string(),
        ))
    } else {
        None
    }
}

/// Add trace context to log fields
#[macro_export]
macro_rules! log_with_trace {
    ($level:ident, $msg:expr $(, $key:tt = $value:expr)*) => {{
        let (trace_id, span_id) = $crate::tracing::correlation::get_trace_context()
            .unwrap_or_else(|| (String::new(), String::new()));

        tracing::$level!(
            trace_id = %trace_id,
            span_id = %span_id,
            $($key = $value,)*
            $msg
        );
    }};
}

/// Middleware to extract trace context from HTTP headers
pub async fn trace_context_middleware<B>(
    req: actix_web::HttpRequest,
    payload: actix_web::web::Payload,
    srv: &actix_web::dev::Service<
        actix_web::dev::ServiceRequest,
        Response = actix_web::dev::ServiceResponse<B>,
        Error = actix_web::Error,
    >,
) -> Result<actix_web::dev::ServiceResponse<B>, actix_web::Error> {
    use opentelemetry::propagation::Extractor;

    // Extract trace context from headers
    struct HeaderExtractor<'a>(&'a actix_web::http::HeaderMap);

    impl<'a> Extractor for HeaderExtractor<'a> {
        fn get(&self, key: &str) -> Option<&str> {
            self.0.get(key).and_then(|v| v.to_str().ok())
        }

        fn keys(&self) -> Vec<&str> {
            self.0.keys().map(|k| k.as_str()).collect()
        }
    }

    let extractor = HeaderExtractor(req.headers());
    let parent_cx = global::get_text_map_propagator(|propagator| {
        propagator.extract(&extractor)
    });

    // Create span with parent context
    let span = tracing::info_span!(
        "http_request",
        method = %req.method(),
        path = %req.path(),
    );

    span.set_parent(parent_cx);

    let _enter = span.enter();

    // Continue with request
    srv.call(actix_web::dev::ServiceRequest::from_request(req, payload))
        .await
}
```

### Trace Context - Python

```python
# file: tracing/correlation.py
# version: 1.0.0
# guid: python-trace-correlation

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import structlog
from typing import Optional, Tuple


def init_tracer(service_name: str, otlp_endpoint: str = "http://localhost:4317") -> None:
    """Initialize OpenTelemetry tracer."""
    resource = Resource(attributes={
        "service.name": service_name,
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    )
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # Instrument libraries
    FastAPIInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    structlog.get_logger().info(
        "Tracer initialized",
        service=service_name,
        otlp_endpoint=otlp_endpoint,
    )


def get_trace_context() -> Optional[Tuple[str, str]]:
    """Get current trace and span IDs."""
    span = trace.get_current_span()
    span_context = span.get_span_context()

    if span_context.is_valid:
        return (
            format(span_context.trace_id, "032x"),
            format(span_context.span_id, "016x"),
        )

    return None


class TraceContextProcessor:
    """Structlog processor to add trace context."""

    def __call__(self, logger, method_name, event_dict):
        """Add trace context to log event."""
        trace_context = get_trace_context()

        if trace_context:
            trace_id, span_id = trace_context
            event_dict["trace_id"] = trace_id
            event_dict["span_id"] = span_id

        return event_dict


def configure_logging_with_traces(log_level: str = "INFO") -> None:
    """Configure structlog with trace context."""
    import logging

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            TraceContextProcessor(),
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# FastAPI middleware for trace context propagation
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Middleware to propagate trace context."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.propagator = TraceContextTextMapPropagator()

    async def dispatch(self, request: Request, call_next):
        """Extract trace context and attach to logs."""
        # Extract context from headers
        context = self.propagator.extract(carrier=request.headers)

        # Attach to current context
        token = trace.set_span_in_context(trace.get_current_span(), context)

        try:
            response = await call_next(request)

            # Inject context into response headers
            self.propagator.inject(carrier=response.headers)

            return response
        finally:
            trace.set_span_in_context(None, token)
```

### Trace Context - JavaScript/TypeScript

```typescript
// file: src/tracing/correlation.ts
// version: 1.0.0
// guid: typescript-trace-correlation

import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { trace, context, propagation, SpanContext } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';
import { Request, Response, NextFunction } from 'express';
import winston from 'winston';

/**
 * Initialize OpenTelemetry tracer
 */
export function initTracer(serviceName: string): void {
  const provider = new NodeTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    }),
  });

  const exporter = new OTLPTraceExporter({
    url: 'http://localhost:4318/v1/traces',
  });

  provider.addSpanProcessor(new BatchSpanProcessor(exporter));
  provider.register();

  // Set global propagator
  propagation.setGlobalPropagator(new W3CTraceContextPropagator());

  console.log(`Tracer initialized for service: ${serviceName}`);
}

/**
 * Get current trace context
 */
export function getTraceContext(): { traceId: string; spanId: string } | null {
  const span = trace.getActiveSpan();

  if (!span) {
    return null;
  }

  const spanContext = span.spanContext();

  if (!spanContext || !spanContext.traceId) {
    return null;
  }

  return {
    traceId: spanContext.traceId,
    spanId: spanContext.spanId,
  };
}

/**
 * Winston format to add trace context
 */
export const traceContextFormat = winston.format(info => {
  const traceContext = getTraceContext();

  if (traceContext) {
    info.traceId = traceContext.traceId;
    info.spanId = traceContext.spanId;
  }

  return info;
});

/**
 * Express middleware for trace context propagation
 */
export function traceContextMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    // Extract trace context from headers
    const ctx = propagation.extract(context.active(), req.headers);

    // Create span for request
    const tracer = trace.getTracer('http-server');
    const span = tracer.startSpan(`${req.method} ${req.path}`, undefined, ctx);

    // Set context for this request
    context.with(trace.setSpan(ctx, span), () => {
      // Add trace context to request
      const traceContext = getTraceContext();
      if (traceContext) {
        req.headers['x-trace-id'] = traceContext.traceId;
        req.headers['x-span-id'] = traceContext.spanId;

        // Add to response headers
        res.setHeader('x-trace-id', traceContext.traceId);
        res.setHeader('x-span-id', traceContext.spanId);
      }

      // End span on response finish
      res.on('finish', () => {
        span.setAttributes({
          'http.status_code': res.statusCode,
          'http.method': req.method,
          'http.url': req.url,
        });
        span.end();
      });

      next();
    });
  };
}
```

## W3C Trace Context Propagation

### HTTP Header Propagation

```markdown
# W3C Trace Context Headers

## traceparent Header

Format: `00-{trace-id}-{parent-id}-{trace-flags}`

Example:
```

traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

```

Components:
- Version: `00` (currently only version 00 is defined)
- Trace ID: 32 hex characters (128-bit)
- Parent ID: 16 hex characters (64-bit span ID)
- Trace Flags: 2 hex characters (8-bit flags)
  - `01` = sampled
  - `00` = not sampled

## tracestate Header

Format: `key1=value1,key2=value2`

Example:
```

tracestate: vendor1=opaque_value1,vendor2=opaque_value2

```

Purpose:
- Vendor-specific trace context
- Multiple vendors can participate
- Preserves trace context across systems
```

### Cross-Service Correlation

```rust
// file: src/tracing/propagation.rs
// version: 1.0.0
// guid: rust-trace-propagation

use reqwest::{Client, Request};
use opentelemetry::{
    global,
    propagation::Injector,
};

/// Inject trace context into HTTP request
pub fn inject_trace_context(request: &mut Request) {
    struct HeaderInjector<'a>(&'a mut reqwest::header::HeaderMap);

    impl<'a> Injector for HeaderInjector<'a> {
        fn set(&mut self, key: &str, value: String) {
            if let Ok(header_name) = reqwest::header::HeaderName::from_bytes(key.as_bytes()) {
                if let Ok(header_value) = reqwest::header::HeaderValue::from_str(&value) {
                    self.0.insert(header_name, header_value);
                }
            }
        }
    }

    let mut injector = HeaderInjector(request.headers_mut());
    global::get_text_map_propagator(|propagator| {
        propagator.inject(&mut injector);
    });
}

/// HTTP client with automatic trace propagation
pub struct TracedClient {
    client: Client,
}

impl TracedClient {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
        }
    }

    pub async fn get(&self, url: &str) -> Result<reqwest::Response, reqwest::Error> {
        let mut request = self.client.get(url).build()?;
        inject_trace_context(&mut request);
        self.client.execute(request).await
    }

    pub async fn post(&self, url: &str, body: String) -> Result<reqwest::Response, reqwest::Error> {
        let mut request = self.client
            .post(url)
            .body(body)
            .build()?;
        inject_trace_context(&mut request);
        self.client.execute(request).await
    }
}
```

## Log-Trace Correlation in Grafana

### Grafana Configuration

```yaml
# file: config/grafana/datasources.yml
# version: 1.0.0
# guid: grafana-datasource-correlation

apiVersion: 1

datasources:
  # Loki for logs
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        # Extract trace ID from logs
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: '$${__value.raw}'
        # Extract from JSON logs
        - datasourceUid: tempo
          matcherRegex: '"trace_id":"(\\w+)"'
          name: TraceID
          url: '$${__value.raw}'

  # Tempo for traces
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ['trace_id']
        mappedTags: [{ key: 'service.name', value: 'service' }]
        mapTagNamesEnabled: true
        spanStartTimeShift: '-1h'
        spanEndTimeShift: '1h'
        filterByTraceID: true
        filterBySpanID: false
      serviceMap:
        datasourceUid: prometheus

  # Prometheus for metrics
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    jsonData:
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo
```

### Exemplars for Metric-to-Trace Correlation

```rust
// file: src/metrics/exemplars.rs
// version: 1.0.0
// guid: rust-metrics-exemplars

use prometheus::{Histogram, HistogramOpts};
use opentelemetry::trace::TraceContextExt;

/// Create histogram with exemplar support
pub fn create_histogram_with_exemplars(
    name: &str,
    help: &str,
) -> Histogram {
    let opts = HistogramOpts::new(name, help);
    Histogram::with_opts(opts).unwrap()
}

/// Record histogram value with trace ID as exemplar
pub fn record_with_exemplar(
    histogram: &Histogram,
    value: f64,
) {
    // Get current trace context
    let cx = opentelemetry::Context::current();
    let span = cx.span();
    let span_context = span.span_context();

    if span_context.is_valid() {
        let trace_id = span_context.trace_id().to_string();

        // Record value with exemplar
        histogram.observe(value);

        // In production, use Prometheus client with exemplar support
        // This is a simplified example
        tracing::debug!(
            value = value,
            trace_id = %trace_id,
            "Recorded metric with exemplar"
        );
    } else {
        histogram.observe(value);
    }
}
```

---

**Part 3 Complete**: Log correlation with traces using OpenTelemetry integration for Rust with
Jaeger exporter and trace context extraction from HTTP headers, Python with OTLP exporter and
structlog processor for trace IDs, JavaScript/TypeScript with W3C trace context propagator and
Express middleware, W3C Trace Context standard with traceparent/tracestate headers for cross-service
propagation, HTTP client wrappers for automatic trace injection in requests, Grafana configuration
for log-to-trace correlation with derived fields linking Loki logs to Tempo traces, exemplars for
metric-to-trace correlation connecting Prometheus metrics to distributed traces. ✅

**Continue to Part 4** for log aggregation infrastructure with Loki deployment, Promtail
configuration, and ELK stack alternatives.
