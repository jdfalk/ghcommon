<!-- file: docs/cross-registry-todos/task-15/t15-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t15-performance-monitoring-part2-w9x0y1z2-a3b4 -->
<!-- last-edited: 2026-01-19 -->

# Task 15 Part 2: JavaScript Instrumentation and System Metrics

## JavaScript/Node.js Performance Instrumentation

### Metrics with prom-client

````typescript
// file: src/metrics.ts
// version: 1.0.0
// guid: typescript-metrics-implementation

import { Registry, Counter, Histogram, Gauge, Summary } from 'prom-client';

/**
 * Metrics registry and collectors for Node.js applications.
 */

// Create registry
export const register = new Registry();

// Enable default metrics (CPU, memory, etc.)
import { collectDefaultMetrics } from 'prom-client';
collectDefaultMetrics({ register });

// HTTP request metrics
export const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status'],
  registers: [register],
});

export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'route'],
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
  registers: [register],
});

// Database metrics
export const dbQueryDuration = new Histogram({
  name: 'db_query_duration_seconds',
  help: 'Database query duration in seconds',
  labelNames: ['operation', 'collection'],
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
  registers: [register],
});

// Active connections
export const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [register],
});

// Error counter
export const errorsTotal = new Counter({
  name: 'errors_total',
  help: 'Total number of errors',
  labelNames: ['type'],
  registers: [register],
});

// Event loop lag
export const eventLoopLag = new Gauge({
  name: 'nodejs_eventloop_lag_seconds',
  help: 'Event loop lag in seconds',
  registers: [register],
});

// Track event loop lag
let lastCheck = Date.now();
setInterval(() => {
  const now = Date.now();
  const lag = (now - lastCheck) / 1000 - 1; // Expected 1 second interval
  eventLoopLag.set(Math.max(0, lag));
  lastCheck = now;
}, 1000);

/**
 * Middleware for Express to automatically collect metrics.
 *
 * @example
 * ```typescript
 * import express from 'express';
 * import { metricsMiddleware } from './metrics';
 *
 * const app = express();
 * app.use(metricsMiddleware);
 * ```
 */
export function metricsMiddleware(req: any, res: any, next: any): void {
  const start = Date.now();

  // Increment active connections
  activeConnections.inc();

  // Track response
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;

    httpRequestsTotal.inc({
      method: req.method,
      route,
      status: res.statusCode,
    });

    httpRequestDuration.observe({ method: req.method, route }, duration);

    // Decrement active connections
    activeConnections.dec();
  });

  next();
}

/**
 * Decorator to time async function execution.
 *
 * @param histogram - Prometheus histogram to record duration
 * @param labels - Labels for the metric
 *
 * @example
 * ```typescript
 * class UserService {
 *   @timeFunction(dbQueryDuration, { operation: 'SELECT', collection: 'users' })
 *   async getUser(id: string): Promise<User> {
 *     // Query logic
 *   }
 * }
 * ```
 */
export function timeFunction(
  histogram: Histogram<string>,
  labels: Record<string, string>
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const end = histogram.startTimer(labels);
      try {
        return await originalMethod.apply(this, args);
      } finally {
        end();
      }
    };

    return descriptor;
  };
}

/**
 * Get metrics in Prometheus text format.
 *
 * @returns Promise resolving to metrics string
 */
export async function getMetrics(): Promise<string> {
  return register.metrics();
}

/**
 * Track custom metric.
 *
 * @param name - Metric name
 * @param value - Metric value
 * @param labels - Optional labels
 */
export function trackCustomMetric(
  name: string,
  value: number,
  labels?: Record<string, string>
): void {
  // Create gauge if doesn't exist
  let gauge = register.getSingleMetric(name) as Gauge<string>;

  if (!gauge) {
    gauge = new Gauge({
      name,
      help: `Custom metric: ${name}`,
      labelNames: labels ? Object.keys(labels) : [],
      registers: [register],
    });
  }

  if (labels) {
    gauge.set(labels, value);
  } else {
    gauge.set(value);
  }
}
````

### OpenTelemetry Tracing for Node.js

````typescript
// file: src/tracing.ts
// version: 1.0.0
// guid: typescript-tracing-implementation

import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';

/**
 * Initialize OpenTelemetry tracing.
 *
 * @param serviceName - Name of the service
 * @param jaegerEndpoint - Jaeger collector endpoint
 */
export function initTracing(
  serviceName: string,
  jaegerEndpoint: string = 'http://localhost:14268/api/traces'
): NodeSDK {
  const sdk = new NodeSDK({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    }),
    traceExporter: new JaegerExporter({
      endpoint: jaegerEndpoint,
    }),
    instrumentations: [
      getNodeAutoInstrumentations({
        // Configure automatic instrumentation
        '@opentelemetry/instrumentation-http': {
          ignoreIncomingPaths: ['/health', '/metrics'],
        },
        '@opentelemetry/instrumentation-express': {
          requestHook: (span, request) => {
            span.setAttribute('http.user_agent', request.headers['user-agent']);
          },
        },
      }),
    ],
  });

  sdk.start();

  console.log(`Tracing initialized for service: ${serviceName}`);

  return sdk;
}

/**
 * Shutdown tracing and flush spans.
 *
 * @param sdk - OpenTelemetry SDK instance
 */
export async function shutdownTracing(sdk: NodeSDK): Promise<void> {
  await sdk.shutdown();
  console.log('Tracing shut down successfully');
}

/**
 * Create a traced async function.
 *
 * @param name - Span name
 * @param fn - Function to trace
 * @returns Traced function
 *
 * @example
 * ```typescript
 * const processUser = traced('process-user', async (userId: string) => {
 *   // Processing logic
 * });
 * ```
 */
export function traced<T extends (...args: any[]) => Promise<any>>(
  name: string,
  fn: T
): T {
  return (async (...args: any[]) => {
    const tracer = trace.getTracer('default');
    return tracer.startActiveSpan(name, async span => {
      try {
        const result = await fn(...args);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : String(error),
        });
        span.recordException(error as Error);
        throw error;
      } finally {
        span.end();
      }
    });
  }) as T;
}

/**
 * Add attributes to current span.
 *
 * @param attributes - Key-value pairs to add
 */
export function addSpanAttributes(
  attributes: Record<string, string | number>
): void {
  const span = trace.getActiveSpan();
  if (span) {
    Object.entries(attributes).forEach(([key, value]) => {
      span.setAttribute(key, value);
    });
  }
}

/**
 * Get current trace context for propagation.
 *
 * @returns Trace context object
 */
export function getCurrentTraceContext(): Record<string, string> {
  const span = trace.getActiveSpan();
  if (!span) {
    return {};
  }

  const spanContext = span.spanContext();
  return {
    'x-trace-id': spanContext.traceId,
    'x-span-id': spanContext.spanId,
  };
}
````

## System-Level Metrics Collection

### Node Exporter Configuration

```yaml
# file: configs/node-exporter.yml
# version: 1.0.0
# guid: node-exporter-configuration

# Node Exporter systemd service
# file: /etc/systemd/system/node-exporter.service
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=node-exporter
Group=node-exporter
ExecStart=/usr/local/bin/node_exporter \
  --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)' \
  --collector.netclass.ignored-devices='^(veth.*|docker.*|br-.*|virbr.*)$$' \
  --collector.cpu \
  --collector.diskstats \
  --collector.filesystem \
  --collector.loadavg \
  --collector.meminfo \
  --collector.netdev \
  --collector.netstat \
  --collector.stat \
  --collector.time \
  --collector.uname \
  --collector.vmstat \
  --web.listen-address=:9100 \
  --web.telemetry-path=/metrics

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Custom System Metrics Collector

```python
#!/usr/bin/env python3
# file: scripts/collect-system-metrics.py
# version: 1.0.0
# guid: system-metrics-collector

"""
Collect custom system-level metrics.

Collects additional system metrics not covered by node_exporter
such as application-specific disk usage, custom process metrics, etc.
"""

import psutil
import time
from prometheus_client import Gauge, CollectorRegistry, push_to_gateway
from typing import Dict, List
import argparse
import logging

logger = logging.getLogger(__name__)


class SystemMetricsCollector:
    """Collects custom system metrics."""

    def __init__(self, registry: CollectorRegistry):
        """
        Initialize system metrics collector.

        Args:
            registry: Prometheus registry
        """
        self.registry = registry

        # Define custom metrics
        self.disk_usage_bytes = Gauge(
            'custom_disk_usage_bytes',
            'Disk usage in bytes',
            ['path'],
            registry=registry
        )

        self.process_count = Gauge(
            'custom_process_count',
            'Number of processes by name',
            ['name'],
            registry=registry
        )

        self.network_connections = Gauge(
            'custom_network_connections',
            'Number of network connections by state',
            ['state'],
            registry=registry
        )

        self.swap_usage_percent = Gauge(
            'custom_swap_usage_percent',
            'Swap usage percentage',
            registry=registry
        )

    def collect_disk_metrics(self, paths: List[str]):
        """
        Collect disk usage metrics.

        Args:
            paths: List of paths to monitor
        """
        for path in paths:
            try:
                usage = psutil.disk_usage(path)
                self.disk_usage_bytes.labels(path=path).set(usage.used)
            except Exception as e:
                logger.error(f"Error collecting disk metrics for {path}: {e}")

    def collect_process_metrics(self, process_names: List[str]):
        """
        Collect process count metrics.

        Args:
            process_names: List of process names to monitor
        """
        process_counts: Dict[str, int] = {name: 0 for name in process_names}

        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if proc_name in process_names:
                    process_counts[proc_name] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        for name, count in process_counts.items():
            self.process_count.labels(name=name).set(count)

    def collect_network_metrics(self):
        """Collect network connection metrics."""
        connections = psutil.net_connections()

        # Count connections by state
        state_counts: Dict[str, int] = {}
        for conn in connections:
            state = conn.status
            state_counts[state] = state_counts.get(state, 0) + 1

        for state, count in state_counts.items():
            self.network_connections.labels(state=state).set(count)

    def collect_swap_metrics(self):
        """Collect swap usage metrics."""
        swap = psutil.swap_memory()
        self.swap_usage_percent.set(swap.percent)

    def collect_all(
        self,
        disk_paths: List[str] = None,
        process_names: List[str] = None
    ):
        """
        Collect all metrics.

        Args:
            disk_paths: Paths to monitor for disk usage
            process_names: Process names to monitor
        """
        if disk_paths:
            self.collect_disk_metrics(disk_paths)

        if process_names:
            self.collect_process_metrics(process_names)

        self.collect_network_metrics()
        self.collect_swap_metrics()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect custom system metrics"
    )
    parser.add_argument(
        '--pushgateway',
        default='localhost:9091',
        help='Pushgateway address'
    )
    parser.add_argument(
        '--job',
        default='system-metrics',
        help='Job name for metrics'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Collection interval in seconds'
    )
    parser.add_argument(
        '--disk-paths',
        nargs='+',
        default=['/'],
        help='Disk paths to monitor'
    )
    parser.add_argument(
        '--process-names',
        nargs='+',
        default=['python', 'node', 'cargo'],
        help='Process names to monitor'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create registry and collector
    registry = CollectorRegistry()
    collector = SystemMetricsCollector(registry)

    logger.info(f"Starting system metrics collection (interval: {args.interval}s)")

    try:
        while True:
            collector.collect_all(
                disk_paths=args.disk_paths,
                process_names=args.process_names
            )

            # Push metrics to pushgateway
            push_to_gateway(
                args.pushgateway,
                job=args.job,
                registry=registry
            )

            logger.info("Metrics pushed to gateway")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == '__main__':
    main()
```

## Continuous Profiling Setup

### Pyroscope Agent Configuration

```yaml
# file: configs/pyroscope-agent.yml
# version: 1.0.0
# guid: pyroscope-agent-configuration

# Pyroscope agent configuration
server:
  address: 'pyroscope-server:4040'

# Application targets
targets:
  - application-name: 'ubuntu-autoinstall-agent'
    spy-name: 'ebpfspy'
    targets:
      - 'localhost:8080'
    labels:
      environment: 'production'
      region: 'us-west-2'

  - application-name: 'python-service'
    spy-name: 'pyspy'
    targets:
      - 'localhost:8000'
    sample-rate: 100
    detect-subprocesses: true

  - application-name: 'node-service'
    spy-name: 'nodespy'
    targets:
      - 'localhost:3000'

# Tags for all profiles
tags:
  cluster: 'production'
  version: 'v1.2.3'
```

### Pyroscope SDK Integration (Python)

```python
#!/usr/bin/env python3
# file: src/profiling.py
# version: 1.0.0
# guid: python-profiling-integration

"""
Continuous profiling with Pyroscope.

Integrates Pyroscope profiling into Python applications for continuous
CPU and memory profiling.
"""

import pyroscope
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def init_profiling(
    application_name: str,
    server_address: str = "http://localhost:4040",
    auth_token: Optional[str] = None,
    tags: Optional[dict] = None
):
    """
    Initialize Pyroscope profiling.

    Args:
        application_name: Name of the application
        server_address: Pyroscope server address
        auth_token: Optional authentication token
        tags: Optional tags for profiles

    Example:
        >>> init_profiling(
        ...     "my-app",
        ...     server_address="https://pyroscope.example.com",
        ...     tags={"environment": "production", "region": "us-west-2"}
        ... )
    """
    config = {
        "application_name": application_name,
        "server_address": server_address,
    }

    if auth_token:
        config["auth_token"] = auth_token

    if tags:
        config["tags"] = tags

    pyroscope.configure(**config)

    logger.info(f"Profiling initialized for {application_name}")


def profile_section(section_name: str):
    """
    Context manager to profile a specific code section.

    Args:
        section_name: Name of the code section

    Example:
        >>> with profile_section("data_processing"):
        ...     # Heavy computation
        ...     process_data()
    """
    return pyroscope.tag_wrapper({
        "section": section_name
    })


# Example usage in application
if __name__ == "__main__":
    # Initialize profiling
    init_profiling(
        "ubuntu-autoinstall-agent",
        server_address="http://pyroscope:4040",
        tags={
            "environment": "production",
            "version": "1.0.0"
        }
    )

    # Profile specific sections
    with profile_section("startup"):
        # Application startup code
        pass

    # Normal application code is automatically profiled
```

### Pyroscope SDK Integration (Node.js)

````typescript
// file: src/profiling.ts
// version: 1.0.0
// guid: typescript-profiling-integration

import Pyroscope from '@pyroscope/nodejs';

/**
 * Initialize Pyroscope profiling for Node.js.
 *
 * @param appName - Application name
 * @param serverAddress - Pyroscope server address
 * @param tags - Optional tags for profiles
 *
 * @example
 * ```typescript
 * initProfiling(
 *   'my-app',
 *   'http://pyroscope:4040',
 *   { environment: 'production', region: 'us-west-2' }
 * );
 * ```
 */
export function initProfiling(
  appName: string,
  serverAddress: string = 'http://localhost:4040',
  tags: Record<string, string> = {}
): void {
  Pyroscope.init({
    appName,
    serverAddress,
    tags,
    sourceMapper: {
      // Map TypeScript source maps for better stack traces
      sourceMapPath: ['./dist'],
    },
  });

  Pyroscope.start();

  console.log(`Profiling initialized for ${appName}`);
}

/**
 * Stop profiling and flush data.
 */
export async function stopProfiling(): Promise<void> {
  await Pyroscope.stop();
  console.log('Profiling stopped');
}

/**
 * Tag a specific code section for profiling.
 *
 * @param tags - Tags for this section
 * @param fn - Function to profile
 *
 * @example
 * ```typescript
 * await profileSection(
 *   { operation: 'data-processing' },
 *   async () => {
 *     // Heavy computation
 *     await processData();
 *   }
 * );
 * ```
 */
export async function profileSection<T>(
  tags: Record<string, string>,
  fn: () => Promise<T>
): Promise<T> {
  return Pyroscope.wrapWithLabels(tags, fn);
}
````

---

**Part 2 Complete**: JavaScript/TypeScript metrics with prom-client, OpenTelemetry tracing for
Node.js, system-level metrics collection with custom collector, node_exporter configuration,
continuous profiling setup with Pyroscope for Python and Node.js. ✅

**Continue to Part 3** for Prometheus configuration, alerting rules, and Grafana dashboards.
