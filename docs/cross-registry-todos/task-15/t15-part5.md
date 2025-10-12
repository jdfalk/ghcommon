<!-- file: docs/cross-registry-todos/task-15/t15-part5.md -->
<!-- version: 1.0.0 -->
<!-- guid: t15-performance-monitoring-part5-m4n5o6p7-q8r9 -->

# Task 15 Part 5: Performance Testing and Benchmarking Automation

## Load Testing with k6

### k6 Test Scripts

```javascript
// file: tests/performance/load/basic-load.js
// version: 1.0.0
// guid: k6-basic-load-test

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const throughput = new Counter('throughput');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 50 }, // Ramp to 50 users
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 100 }, // Spike to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '5m', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  // Health check
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status is 200': r => r.status === 200,
  });

  // API endpoint test
  let apiRes = http.get(`${BASE_URL}/api/v1/status`);
  const success = check(apiRes, {
    'status is 200': r => r.status === 200,
    'response time < 500ms': r => r.timings.duration < 500,
    'has valid JSON': r => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
  });

  // Record metrics
  errorRate.add(!success);
  responseTime.add(apiRes.timings.duration);
  throughput.add(1);

  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance/results/load-test-summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

```javascript
// file: tests/performance/load/stress-test.js
// version: 1.0.0
// guid: k6-stress-test

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5m', target: 100 }, // Ramp up to normal load
    { duration: '10m', target: 100 }, // Sustain normal load
    { duration: '5m', target: 200 }, // Ramp to stress level
    { duration: '10m', target: 200 }, // Sustain stress
    { duration: '5m', target: 400 }, // Beyond breaking point
    { duration: '10m', target: 400 }, // Sustain maximum
    { duration: '10m', target: 0 }, // Recovery
  ],
  thresholds: {
    http_req_duration: ['p(99)<2000'], // More lenient for stress test
    http_req_failed: ['rate<0.10'], // Allow higher failure rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const responses = http.batch([
    ['GET', `${BASE_URL}/api/v1/images`],
    ['GET', `${BASE_URL}/api/v1/status`],
    [
      'POST',
      `${BASE_URL}/api/v1/validate`,
      JSON.stringify({
        version: '24.04',
        architecture: 'amd64',
      }),
      {
        headers: { 'Content-Type': 'application/json' },
      },
    ],
  ]);

  responses.forEach(response => {
    check(response, {
      'status is 2xx or 5xx': r => r.status >= 200 && r.status < 600,
    });
  });

  sleep(Math.random() * 3);
}
```

```javascript
// file: tests/performance/load/spike-test.js
// version: 1.0.0
// guid: k6-spike-test

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Baseline
    { duration: '1m', target: 1000 }, // Sudden spike
    { duration: '3m', target: 1000 }, // Sustain spike
    { duration: '2m', target: 100 }, // Return to baseline
    { duration: '1m', target: 0 }, // Recovery
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.15'], // More lenient for spike
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const res = http.get(`${BASE_URL}/api/v1/status`);
  check(res, {
    'survived spike': r => r.status < 500 || r.status === 503,
  });
}
```

### k6 GitHub Actions Integration

```yaml
# file: .github/workflows/performance-testing.yml
# version: 1.0.0
# guid: workflow-performance-testing

name: Performance Testing

on:
  schedule:
    - cron: '0 2 * * 0' # Weekly on Sunday at 2 AM
  workflow_dispatch:
    inputs:
      test_type:
        description: 'Type of performance test'
        required: true
        type: choice
        options:
          - load
          - stress
          - spike
          - soak
      duration:
        description: 'Test duration (for soak test)'
        required: false
        default: '1h'

jobs:
  performance-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
            sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Start application
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 10
          curl -f http://localhost:8080/health || exit 1

      - name: Run load test
        if: github.event.inputs.test_type == 'load' || github.event.inputs.test_type == ''
        run: |
          k6 run \
            --out json=performance/results/load-test.json \
            --summary-export=performance/results/load-test-summary.json \
            tests/performance/load/basic-load.js

      - name: Run stress test
        if: github.event.inputs.test_type == 'stress'
        run: |
          k6 run \
            --out json=performance/results/stress-test.json \
            tests/performance/load/stress-test.js

      - name: Run spike test
        if: github.event.inputs.test_type == 'spike'
        run: |
          k6 run \
            --out json=performance/results/spike-test.json \
            tests/performance/load/spike-test.js

      - name: Run soak test
        if: github.event.inputs.test_type == 'soak'
        run: |
          k6 run \
            --duration ${{ github.event.inputs.duration }} \
            --vus 50 \
            --out json=performance/results/soak-test.json \
            tests/performance/load/basic-load.js

      - name: Upload results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: performance-results-${{ github.event.inputs.test_type || 'load' }}
          path: performance/results/

      - name: Export to Prometheus
        if: always()
        run: |
          python3 scripts/export-k6-metrics.py \
            performance/results/load-test.json \
            --pushgateway-url http://pushgateway:9091

      - name: Check thresholds
        run: |
          python3 scripts/check-performance-thresholds.py \
            performance/results/load-test-summary.json \
            --fail-on-breach
```

## Rust Criterion Benchmarks

### Benchmark Configuration

```rust
// file: benches/disk_manager_bench.rs
// version: 1.0.0
// guid: criterion-disk-manager-bench

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use ubuntu_autoinstall_agent::disk::DiskManager;
use tempfile::TempDir;

fn disk_create_benchmark(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();

    c.bench_function("disk_create_10gb", |b| {
        b.iter(|| {
            let disk_manager = DiskManager::new(temp_dir.path()).unwrap();
            disk_manager.create_disk(black_box(10 * 1024 * 1024 * 1024)).unwrap();
        });
    });
}

fn disk_validation_benchmark(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();
    let disk_manager = DiskManager::new(temp_dir.path()).unwrap();
    let disk_path = disk_manager.create_disk(1024 * 1024 * 1024).unwrap();

    c.bench_function("disk_validate", |b| {
        b.iter(|| {
            disk_manager.validate_disk(black_box(&disk_path)).unwrap();
        });
    });
}

fn disk_size_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("disk_create_scaling");

    for size_gb in [1, 5, 10, 20, 50].iter() {
        group.bench_with_input(
            BenchmarkId::from_parameter(size_gb),
            size_gb,
            |b, &size| {
                let temp_dir = TempDir::new().unwrap();
                let disk_manager = DiskManager::new(temp_dir.path()).unwrap();
                b.iter(|| {
                    disk_manager.create_disk(black_box(size * 1024 * 1024 * 1024)).unwrap();
                });
            },
        );
    }

    group.finish();
}

criterion_group!(
    benches,
    disk_create_benchmark,
    disk_validation_benchmark,
    disk_size_scaling
);
criterion_main!(benches);
```

```rust
// file: benches/iso_manager_bench.rs
// version: 1.0.0
// guid: criterion-iso-manager-bench

use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};
use ubuntu_autoinstall_agent::iso::{IsoManager, UbuntuVersion};

fn url_generation_benchmark(c: &mut Criterion) {
    let iso_manager = IsoManager::new();

    c.bench_function("iso_url_generation", |b| {
        b.iter(|| {
            iso_manager.get_iso_url(&UbuntuVersion::V2404, "amd64").unwrap();
        });
    });
}

fn version_comparison_benchmark(c: &mut Criterion) {
    let mut group = c.benchmark_group("iso_version_comparison");

    let versions = vec![
        UbuntuVersion::V2004,
        UbuntuVersion::V2204,
        UbuntuVersion::V2404,
    ];

    for version in versions.iter() {
        group.bench_with_input(
            BenchmarkId::from_parameter(format!("{:?}", version)),
            version,
            |b, version| {
                let iso_manager = IsoManager::new();
                b.iter(|| {
                    iso_manager.get_iso_url(version, "amd64").unwrap();
                });
            },
        );
    }

    group.finish();
}

criterion_group!(benches, url_generation_benchmark, version_comparison_benchmark);
criterion_main!(benches);
```

### Criterion Configuration

```toml
# file: benches/criterion.toml
# version: 1.0.0
# guid: criterion-configuration

[criterion]
# Confidence level for statistical tests
confidence_level = 0.95

# Number of warm-up iterations
warm_up_time = 3

# Measurement time per benchmark
measurement_time = 5

# Number of samples to collect
sample_size = 100

# Noise threshold for detecting performance changes
noise_threshold = 0.02

# Output directory for benchmark results
output_directory = "target/criterion"
```

### Benchmark CI Integration

```yaml
# file: .github/workflows/benchmarks.yml
# version: 1.0.0
# guid: workflow-rust-benchmarks

name: Rust Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0' # Weekly

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: actions-rust-lang/setup-rust-toolchain@v1
        with:
          toolchain: stable

      - name: Cache cargo registry
        uses: actions/cache@v4
        with:
          path: ~/.cargo/registry
          key: ${{ runner.os }}-cargo-registry-${{ hashFiles('**/Cargo.lock') }}

      - name: Run benchmarks
        run: cargo bench --all-features -- --output-format bencher | tee output.txt

      - name: Store benchmark result
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'cargo'
          output-file-path: output.txt
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
          alert-threshold: '150%'
          comment-on-alert: true
          fail-on-alert: false

      - name: Upload criterion results
        uses: actions/upload-artifact@v4
        with:
          name: criterion-results
          path: target/criterion/
```

## Python Performance Testing

### pytest-benchmark Configuration

```python
# file: tests/performance/test_benchmarks.py
# version: 1.0.0
# guid: pytest-benchmark-tests

import pytest
from ubuntu_autoinstall.config import ConfigGenerator
from ubuntu_autoinstall.validation import ConfigValidator

@pytest.fixture
def sample_config():
    """Sample configuration for benchmarking."""
    return {
        'version': 1,
        'locale': 'en_US.UTF-8',
        'keyboard': {'layout': 'us'},
        'network': {
            'version': 2,
            'ethernets': {
                'eth0': {
                    'dhcp4': True,
                }
            }
        },
        'storage': {
            'layout': {
                'name': 'lvm',
            }
        },
    }

def test_config_generation(benchmark, sample_config):
    """Benchmark configuration generation."""
    generator = ConfigGenerator()
    result = benchmark(generator.generate, sample_config)
    assert result is not None

def test_config_validation(benchmark, sample_config):
    """Benchmark configuration validation."""
    validator = ConfigValidator()
    result = benchmark(validator.validate, sample_config)
    assert result.is_valid

@pytest.mark.parametrize("network_count", [1, 5, 10, 20])
def test_config_scaling(benchmark, sample_config, network_count):
    """Benchmark configuration with varying network interface counts."""
    config = sample_config.copy()
    config['network']['ethernets'] = {
        f'eth{i}': {'dhcp4': True}
        for i in range(network_count)
    }

    generator = ConfigGenerator()
    result = benchmark(generator.generate, config)
    assert len(result['network']['ethernets']) == network_count

class TestConfigPerformance:
    """Performance test suite for configuration operations."""

    def test_large_config_generation(self, benchmark):
        """Test generation of large configuration files."""
        config = {
            'version': 1,
            'storage': {
                'config': [
                    {
                        'type': 'disk',
                        'id': f'disk{i}',
                        'path': f'/dev/sd{chr(97+i)}',
                    }
                    for i in range(100)
                ]
            }
        }

        generator = ConfigGenerator()
        result = benchmark(generator.generate, config)
        assert len(result['storage']['config']) == 100

    @pytest.mark.benchmark(
        group="validation",
        min_rounds=50,
        timer=time.perf_counter,
        disable_gc=True,
        warmup=True
    )
    def test_validation_performance(self, benchmark, sample_config):
        """Detailed validation performance test."""
        validator = ConfigValidator()
        stats = benchmark.pedantic(
            validator.validate,
            args=(sample_config,),
            iterations=10,
            rounds=50
        )
```

### pytest-benchmark Configuration

```ini
# file: pytest.ini
# version: 1.0.0
# guid: pytest-benchmark-config

[pytest]
addopts =
    --benchmark-only
    --benchmark-warmup=on
    --benchmark-autosave
    --benchmark-save-data
    --benchmark-compare
    --benchmark-histogram

[tool:pytest]
benchmark_min_rounds = 5
benchmark_min_time = 0.000005
benchmark_max_time = 1.0
benchmark_timer = time.perf_counter
benchmark_disable_gc = true
benchmark_warmup = true
benchmark_warmup_iterations = 10000
```

## Performance Regression Detection

### Python Script for Threshold Checking

```python
#!/usr/bin/env python3
# file: scripts/check-performance-thresholds.py
# version: 1.0.0
# guid: performance-threshold-checker

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceThreshold:
    """Performance threshold definition."""
    metric: str
    operator: str  # 'lt', 'lte', 'gt', 'gte'
    value: float
    percentile: int = 95

@dataclass
class ThresholdViolation:
    """Threshold violation details."""
    metric: str
    expected: float
    actual: float
    operator: str

class ThresholdChecker:
    """Check performance test results against defined thresholds."""

    DEFAULT_THRESHOLDS = [
        PerformanceThreshold('http_req_duration', 'lte', 500, 95),
        PerformanceThreshold('http_req_duration', 'lte', 1000, 99),
        PerformanceThreshold('http_req_failed', 'lte', 0.01),
        PerformanceThreshold('http_reqs', 'gte', 100),  # Min 100 req/s
    ]

    def __init__(self, thresholds: List[PerformanceThreshold] = None):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

    def check(self, results: Dict) -> List[ThresholdViolation]:
        """Check results against thresholds."""
        violations = []

        for threshold in self.thresholds:
            actual = self._extract_metric(results, threshold)
            if actual is None:
                continue

            if not self._evaluate_threshold(actual, threshold):
                violations.append(ThresholdViolation(
                    metric=threshold.metric,
                    expected=threshold.value,
                    actual=actual,
                    operator=threshold.operator
                ))

        return violations

    def _extract_metric(self, results: Dict, threshold: PerformanceThreshold) -> float:
        """Extract metric value from results."""
        try:
            metric_data = results['metrics'][threshold.metric]

            if threshold.percentile:
                # Extract percentile value
                percentile_key = f'p({threshold.percentile})'
                return metric_data['values'][percentile_key]
            else:
                # Extract rate or count
                return metric_data.get('rate', metric_data.get('count'))
        except (KeyError, TypeError):
            return None

    def _evaluate_threshold(self, actual: float, threshold: PerformanceThreshold) -> bool:
        """Evaluate if actual value meets threshold."""
        operators = {
            'lt': lambda a, e: a < e,
            'lte': lambda a, e: a <= e,
            'gt': lambda a, e: a > e,
            'gte': lambda a, e: a >= e,
        }

        return operators[threshold.operator](actual, threshold.value)

def main():
    parser = argparse.ArgumentParser(description='Check performance test thresholds')
    parser.add_argument('results_file', help='Path to k6 results JSON file')
    parser.add_argument('--fail-on-breach', action='store_true',
                       help='Exit with error code if thresholds breached')
    parser.add_argument('--baseline', help='Baseline results for comparison')
    args = parser.parse_args()

    # Load results
    with open(args.results_file) as f:
        results = json.load(f)

    # Check thresholds
    checker = ThresholdChecker()
    violations = checker.check(results)

    # Report violations
    if violations:
        print("⚠️  Performance threshold violations detected:")
        for violation in violations:
            print(f"  {violation.metric}: {violation.actual:.2f} "
                  f"{violation.operator} {violation.expected:.2f}")

        if args.fail_on_breach:
            sys.exit(1)
    else:
        print("✅ All performance thresholds met")

    # Compare with baseline if provided
    if args.baseline:
        with open(args.baseline) as f:
            baseline = json.load(f)
        compare_with_baseline(results, baseline)

def compare_with_baseline(current: Dict, baseline: Dict):
    """Compare current results with baseline."""
    print("\n📊 Performance comparison with baseline:")

    for metric_name in ['http_req_duration', 'http_req_failed', 'http_reqs']:
        current_value = current['metrics'][metric_name]['values']['p(95)']
        baseline_value = baseline['metrics'][metric_name]['values']['p(95)']

        diff_percent = ((current_value - baseline_value) / baseline_value) * 100

        indicator = "🔴" if diff_percent > 10 else "🟡" if diff_percent > 5 else "🟢"

        print(f"  {indicator} {metric_name}: {current_value:.2f} "
              f"({diff_percent:+.1f}% vs baseline {baseline_value:.2f})")

if __name__ == '__main__':
    main()
```

### Export k6 Metrics to Prometheus

```python
#!/usr/bin/env python3
# file: scripts/export-k6-metrics.py
# version: 1.0.0
# guid: k6-prometheus-exporter

import argparse
import json
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def export_k6_metrics(results_file: str, pushgateway_url: str, job_name: str = 'k6'):
    """Export k6 test results to Prometheus Pushgateway."""
    registry = CollectorRegistry()

    # Load k6 results
    with open(results_file) as f:
        results = json.load(f)

    # Create gauges for key metrics
    metrics = {
        'http_req_duration_p95': Gauge(
            'k6_http_req_duration_p95_seconds',
            'HTTP request duration 95th percentile',
            ['test_name'],
            registry=registry
        ),
        'http_req_duration_p99': Gauge(
            'k6_http_req_duration_p99_seconds',
            'HTTP request duration 99th percentile',
            ['test_name'],
            registry=registry
        ),
        'http_req_failed_rate': Gauge(
            'k6_http_req_failed_rate',
            'HTTP request failure rate',
            ['test_name'],
            registry=registry
        ),
        'http_reqs_rate': Gauge(
            'k6_http_reqs_per_second',
            'HTTP requests per second',
            ['test_name'],
            registry=registry
        ),
        'vus_max': Gauge(
            'k6_vus_max',
            'Maximum virtual users',
            ['test_name'],
            registry=registry
        ),
    }

    test_name = results.get('test_name', 'load_test')

    # Set metric values
    duration_p95 = results['metrics']['http_req_duration']['values']['p(95)'] / 1000
    duration_p99 = results['metrics']['http_req_duration']['values']['p(99)'] / 1000
    failed_rate = results['metrics']['http_req_failed']['values']['rate']
    req_rate = results['metrics']['http_reqs']['values']['rate']
    vus = results['metrics']['vus_max']['values']['max']

    metrics['http_req_duration_p95'].labels(test_name=test_name).set(duration_p95)
    metrics['http_req_duration_p99'].labels(test_name=test_name).set(duration_p99)
    metrics['http_req_failed_rate'].labels(test_name=test_name).set(failed_rate)
    metrics['http_reqs_rate'].labels(test_name=test_name).set(req_rate)
    metrics['vus_max'].labels(test_name=test_name).set(vus)

    # Push to gateway
    push_to_gateway(pushgateway_url, job=job_name, registry=registry)

    print(f"✅ Exported k6 metrics to {pushgateway_url}")

def main():
    parser = argparse.ArgumentParser(description='Export k6 metrics to Prometheus')
    parser.add_argument('results_file', help='Path to k6 results JSON')
    parser.add_argument('--pushgateway-url', required=True,
                       help='Prometheus Pushgateway URL')
    parser.add_argument('--job-name', default='k6',
                       help='Job name for Pushgateway')
    args = parser.parse_args()

    export_k6_metrics(args.results_file, args.pushgateway_url, args.job_name)

if __name__ == '__main__':
    main()
```

---

**Part 5 Complete**: Performance testing automation with k6 load/stress/spike tests, Rust Criterion
benchmarks with scaling tests, Python pytest-benchmark integration, performance regression detection
with threshold checking, and k6 metrics export to Prometheus. ✅

**Continue to Part 6** for monitoring best practices and completion checklist.
