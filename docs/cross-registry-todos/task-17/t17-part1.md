<!-- file: docs/cross-registry-todos/task-17/t17-part1.md -->
<!-- version: 1.0.0 -->
<!-- guid: t17-observability-logging-part1-i2j3k4l5-m6n7 -->

# Task 17 Part 1: Structured Logging Standards Across All Languages

## Structured Logging Strategy

### Logging Levels and Usage

```markdown
# Logging Level Guidelines

## TRACE
**Purpose**: Extremely detailed diagnostic information
**Use cases**:
- Function entry/exit with parameters
- Loop iterations with values
- Detailed state transitions
**Environment**: Development/debugging only
**Example**: "Entering process_request with user_id=123, request_id=abc-456"

## DEBUG
**Purpose**: Detailed information for debugging
**Use cases**:
- Variable values at key points
- Conditional branch taken
- Cache hits/misses
- Database query parameters
**Environment**: Development, staging
**Example**: "Cache miss for key 'user:123', fetching from database"

## INFO
**Purpose**: General informational messages
**Use cases**:
- Application startup/shutdown
- Configuration loaded
- Successful operations
- Business event milestones
**Environment**: All environments
**Example**: "Application started on port 8080 with 4 workers"

## WARN
**Purpose**: Potentially harmful situations
**Use cases**:
- Deprecated API usage
- Suboptimal performance
- Recoverable errors
- Approaching resource limits
**Environment**: All environments
**Example**: "Connection pool at 80% capacity (40/50 connections used)"

## ERROR
**Purpose**: Error events that might still allow application to continue
**Use cases**:
- Handled exceptions
- Failed external API calls with retry
- Validation failures
- Resource not found
**Environment**: All environments
**Example**: "Failed to fetch user profile from API: timeout after 30s, will retry"

## FATAL/CRITICAL
**Purpose**: Severe errors that cause application termination
**Use cases**:
- Database connection lost
- Critical configuration missing
- Unrecoverable system errors
**Environment**: All environments
**Example**: "Cannot connect to database after 5 retries, shutting down"
```

## Rust Structured Logging

### Tracing Configuration

```rust
// file: src/logging.rs
// version: 1.0.0
// guid: rust-logging-config

use tracing::{info, warn, error, debug, Level};
use tracing_subscriber::{
    fmt::{self, format::FmtSpan},
    layer::SubscriberExt,
    util::SubscriberInitExt,
    EnvFilter,
};
use tracing_appender::{non_blocking, rolling};
use serde::Serialize;
use std::io;

/// Initialize structured logging with JSON formatting
pub fn init_logging(log_level: &str, log_file: Option<&str>) -> Result<(), Box<dyn std::error::Error>> {
    // Environment filter for log level
    let env_filter = EnvFilter::try_from_default_env()
        .or_else(|_| EnvFilter::try_new(log_level))?;

    // JSON formatter
    let fmt_layer = fmt::layer()
        .json()
        .with_current_span(true)
        .with_span_list(true)
        .with_thread_ids(true)
        .with_thread_names(true)
        .with_target(true)
        .with_file(true)
        .with_line_number(true)
        .with_span_events(FmtSpan::CLOSE);

    // Build subscriber
    match log_file {
        Some(path) => {
            // File appender with daily rotation
            let file_appender = rolling::daily("logs", path);
            let (non_blocking, _guard) = non_blocking(file_appender);

            tracing_subscriber::registry()
                .with(env_filter)
                .with(fmt_layer.with_writer(non_blocking))
                .init();
        }
        None => {
            // Console output
            tracing_subscriber::registry()
                .with(env_filter)
                .with(fmt_layer.with_writer(io::stdout))
                .init();
        }
    }

    info!(
        version = env!("CARGO_PKG_VERSION"),
        log_level = log_level,
        "Logging initialized"
    );

    Ok(())
}

/// Structured log fields for HTTP requests
#[derive(Debug, Serialize)]
pub struct HttpRequestLog {
    pub method: String,
    pub path: String,
    pub status: u16,
    pub duration_ms: u64,
    pub user_id: Option<String>,
    pub request_id: String,
    pub remote_addr: String,
    pub user_agent: Option<String>,
}

/// Structured log fields for database operations
#[derive(Debug, Serialize)]
pub struct DatabaseLog {
    pub operation: String,
    pub table: String,
    pub duration_ms: u64,
    pub rows_affected: Option<i64>,
    pub error: Option<String>,
}

/// Log HTTP request with structured fields
#[tracing::instrument(
    skip(request),
    fields(
        http.method = %request.method,
        http.path = %request.path,
        http.status = tracing::field::Empty,
        http.duration_ms = tracing::field::Empty,
    )
)]
pub async fn log_http_request<T>(
    request: HttpRequest,
    handler: impl FnOnce(HttpRequest) -> T,
) -> T {
    let start = std::time::Instant::now();
    let method = request.method.clone();
    let path = request.path.clone();

    let response = handler(request);

    let duration = start.elapsed().as_millis() as u64;

    tracing::Span::current().record("http.duration_ms", duration);

    info!(
        method = %method,
        path = %path,
        duration_ms = duration,
        "HTTP request completed"
    );

    response
}
```

### Actix-Web Middleware

```rust
// file: src/middleware/logging.rs
// version: 1.0.0
// guid: rust-actix-logging-middleware

use actix_web::{
    dev::{forward_ready, Service, ServiceRequest, ServiceResponse, Transform},
    Error, HttpMessage,
};
use futures_util::future::LocalBoxFuture;
use std::future::{ready, Ready};
use std::time::Instant;
use tracing::{info, warn, error, Span};
use uuid::Uuid;

/// Logging middleware for Actix-Web
pub struct LoggingMiddleware;

impl<S, B> Transform<S, ServiceRequest> for LoggingMiddleware
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error>,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type InitError = ();
    type Transform = LoggingMiddlewareService<S>;
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        ready(Ok(LoggingMiddlewareService { service }))
    }
}

pub struct LoggingMiddlewareService<S> {
    service: S,
}

impl<S, B> Service<ServiceRequest> for LoggingMiddlewareService<S>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error>,
    S::Future: 'static,
    B: 'static,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    forward_ready!(service);

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let start = Instant::now();

        // Generate request ID
        let request_id = Uuid::new_v4().to_string();
        req.extensions_mut().insert(request_id.clone());

        // Extract request info
        let method = req.method().to_string();
        let path = req.path().to_string();
        let remote_addr = req.peer_addr().map(|a| a.to_string());
        let user_agent = req
            .headers()
            .get("user-agent")
            .and_then(|h| h.to_str().ok())
            .map(|s| s.to_string());

        // Create span for request
        let span = tracing::info_span!(
            "http_request",
            http.method = %method,
            http.path = %path,
            http.status = tracing::field::Empty,
            http.duration_ms = tracing::field::Empty,
            request_id = %request_id,
            remote_addr = remote_addr.as_deref(),
            user_agent = user_agent.as_deref(),
        );

        let _enter = span.enter();

        let fut = self.service.call(req);

        Box::pin(async move {
            let res = fut.await?;

            let duration = start.elapsed().as_millis() as u64;
            let status = res.status().as_u16();

            // Record fields
            Span::current().record("http.status", status);
            Span::current().record("http.duration_ms", duration);

            // Log based on status
            if status >= 500 {
                error!(
                    method = %method,
                    path = %path,
                    status = status,
                    duration_ms = duration,
                    request_id = %request_id,
                    "HTTP request failed with server error"
                );
            } else if status >= 400 {
                warn!(
                    method = %method,
                    path = %path,
                    status = status,
                    duration_ms = duration,
                    request_id = %request_id,
                    "HTTP request failed with client error"
                );
            } else {
                info!(
                    method = %method,
                    path = %path,
                    status = status,
                    duration_ms = duration,
                    request_id = %request_id,
                    "HTTP request completed successfully"
                );
            }

            Ok(res)
        })
    }
}
```

## Python Structured Logging

### Structlog Configuration

```python
# file: logging_config.py
# version: 1.0.0
# guid: python-logging-config

import logging
import logging.config
import sys
from typing import Any, Dict

import structlog
from structlog.processors import (
    TimeStamper,
    StackInfoRenderer,
    format_exc_info,
    UnicodeDecoder,
    CallsiteParameterAdder,
)
from structlog.stdlib import (
    add_log_level,
    add_logger_name,
    ProcessorFormatter,
)


def configure_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
    json_format: bool = True
) -> None:
    """Configure structured logging with structlog."""

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_log_level,
        add_logger_name,
        TimeStamper(fmt="iso", utc=True),
        StackInfoRenderer(),
        format_exc_info,
        UnicodeDecoder(),
    ]

    if json_format:
        # JSON output
        structlog.configure(
            processors=shared_processors + [
                CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                ),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Console output with colors
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configure stdlib logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": ProcessorFormatter,
                "processors": shared_processors + [
                    structlog.processors.JSONRenderer(),
                ],
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            },
        },
        "root": {
            "level": log_level.upper(),
            "handlers": ["console"],
        },
    }

    if log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": log_file,
            "maxBytes": 10_485_760,  # 10MB
            "backupCount": 5,
        }
        logging_config["root"]["handlers"].append("file")

    logging.config.dictConfig(logging_config)

    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        log_level=log_level,
        json_format=json_format,
        log_file=log_file,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Context manager for adding context
class log_context:
    """Context manager for adding context to all logs."""

    def __init__(self, **kwargs: Any):
        self.context = kwargs
        self.token = None

    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())
        return False
```

### FastAPI Middleware

```python
# file: middleware/logging.py
# version: 1.0.0
# guid: python-fastapi-logging-middleware

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for FastAPI."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Bind context for this request
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            remote_addr=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Add request ID to headers
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log based on status
            log_func = logger.info
            if response.status_code >= 500:
                log_func = logger.error
            elif response.status_code >= 400:
                log_func = logger.warning

            log_func(
                "HTTP request completed",
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "HTTP request failed",
                status=500,
                duration_ms=round(duration_ms, 2),
                error=str(exc),
                exc_info=True,
            )

            raise

        finally:
            # Unbind context
            structlog.contextvars.unbind_contextvars(
                "request_id",
                "method",
                "path",
                "remote_addr",
                "user_agent",
            )
```

---

**Part 1 Complete**: Structured logging standards with comprehensive logging level guidelines (TRACE
through FATAL), Rust tracing configuration with JSON formatting and daily rotation, Actix-Web logging
middleware with request IDs and span tracking, Python structlog configuration with JSON output and
context managers, FastAPI logging middleware with automatic context binding and request ID propagation. ✅

**Continue to Part 2** for JavaScript/TypeScript logging with Winston and Pino, log correlation with
trace IDs, and log enrichment strategies.
