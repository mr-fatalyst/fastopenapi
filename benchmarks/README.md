# Benchmarks

## Overview

This benchmark suite compares the performance of different Python web frameworks with three implementation variants:

- **Pure**: Minimal implementation without validation - raw framework performance
- **with_validators**: Adds Pydantic validation for request/response models
- **with_fastopenapi**: Uses FastOpenAPI router with automatic OpenAPI documentation and validation
- **FastAPI** (baseline): Industry-standard async framework for comparison

Each implementation runs as a separate application, and the benchmark measures throughput (RPS) and latency across all CRUD endpoints.

## Supported Frameworks

- [AioHttp](aiohttp/AIOHTTP.md) - Async
- [Django](django/DJANGO.md) - Sync (WSGI)
- [Falcon](falcon/FALCON.md) - Sync (WSGI)
- [Flask](flask/FLASK.md) - Sync (WSGI)
- [Quart](quart/QUART.md) - Async
- [Sanic](sanic/SANIC.md) - Async
- [Starlette](starlette/STARLETTE.md) - Async
- [Tornado](tornado/TORNADO.md) - Async

## How It Works

### Test Parameters
- **10,000 requests** per endpoint (configurable)
- **100 warmup requests** per endpoint
- **20 concurrent requests** (configurable)
- **5 rounds** with randomized order to reduce bias
- **Median values** used for final comparison

### Endpoints Tested
- `GET /records` - List all records
- `GET /records/{id}` - Get single record
- `POST /records` - Create new record
- `PUT /records/{id}` - Replace entire record
- `PATCH /records/{id}` - Partial update
- `DELETE /records/{id}` - Delete record (creates records first)

### Metrics Reported
- **RPS** (Requests Per Second) - Higher is better
- **Mean latency** - Average response time
- **p50** (median) - 50th percentile latency
- **p95** - 95th percentile latency
- **p99** - 99th percentile latency
- **Min/Max** - Best and worst latencies

## Running the Benchmark

### 1. Start all implementations

For each framework, start all three variants:

```bash
# Pure implementation (port 8000)
python benchmarks/<framework>/pure.py

# With validators (port 8001)
python benchmarks/<framework>/with_validators.py

# With FastOpenAPI (port 8002)
python benchmarks/<framework>/with_fastopenapi.py

# FastAPI for comparison (port 8003)
python benchmarks/fastapi/run.py
```

Example for AioHttp:
```bash
python benchmarks/aiohttp/pure.py
python benchmarks/aiohttp/with_validators.py
python benchmarks/aiohttp/with_fastopenapi.py
python benchmarks/fastapi/run.py
```

### 2. Run the benchmark

```bash
python benchmarks/common/benchmark.py
```

The benchmark will:
1. Run 5 rounds in randomized order
2. Display results for each round
3. Calculate median values across rounds
4. Compare all implementations with Pure as baseline

## Example Output

### Per-Round Results

```markdown
================================================================================

## Framework Pure (round 1)
Concurrency: **20**

| Endpoint | RPS | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
|:---------|----:|----------:|---------:|---------:|---------:|---------:|---------:|
| `GET all records` | 45230 | 2.21 | 2.10 | 3.50 | 4.80 | 1.20 | 8.50 |
| `GET one record` | 46890 | 2.13 | 2.05 | 3.30 | 4.60 | 1.15 | 7.80 |
| `POST new record` | 38450 | 2.60 | 2.45 | 4.10 | 5.90 | 1.40 | 10.20 |
| `PUT record` | 42100 | 2.37 | 2.25 | 3.80 | 5.30 | 1.30 | 9.10 |
| `PATCH record` | 43200 | 2.31 | 2.20 | 3.70 | 5.10 | 1.25 | 8.80 |
| `DELETE record` | 41500 | 2.41 | 2.30 | 3.85 | 5.40 | 1.35 | 9.50 |
```

### Median Summary

```markdown
================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 45180 | 3.48 |
| `GET one record` | 46820 | 3.28 |
| `POST new record` | 38390 | 4.08 |
| `PUT record` | 42050 | 3.78 |
| `PATCH record` | 43150 | 3.68 |
| `DELETE record` | 41450 | 3.82 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 42300 | 3.75 |
| `GET one record` | 43950 | 3.58 |
...
```

### Performance Comparison

```markdown
================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 45180 | 42300 | -6.4% | 41200 | -8.8% | 40500 | -10.4% |
| `GET one record` | 46820 | 43950 | -6.1% | 42800 | -8.6% | 41900 | -10.5% |
| `POST new record` | 38390 | 35200 | -8.3% | 34100 | -11.2% | 33500 | -12.7% |
...

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 3.48 | 3.75 | +7.8% | 3.92 | +12.6% | 4.05 | +16.4% |
| `GET one record` | 3.28 | 3.58 | +9.1% | 3.78 | +15.2% | 3.95 | +20.4% |
...
```

## Benchmark Structure

```
benchmarks/
├── common/
│   ├── benchmark_base.py    # Core benchmark logic
│   ├── schemas.py            # Pydantic models
│   └── storage.py            # In-memory store
├── aiohttp/
│   ├── pure.py
│   ├── with_validators.py
│   └── with_fastopenapi.py
├── django/
│   ├── pure.py
│   ├── with_validators.py
│   └── with_fastopenapi.py
├── falcon/
│   ├── pure.py
│   ├── with_validators.py
│   └── with_fastopenapi.py
... (other frameworks)
└── benchmark.py          # Main runner script
```

## Interpreting Results

### Pure Performance
Shows the raw framework overhead - routing, parsing, serialization. This is the baseline (100%).

### Validators Overhead
Shows the cost of adding Pydantic validation:
- Input validation (request models)
- Output validation (response models)
- Typically 5-15% overhead

### FastOpenAPI Overhead
Shows the cost of adding automatic OpenAPI documentation generation:
- Router proxy layer
- Schema extraction
- Documentation generation
- Typically 8-20% overhead on top of pure

### FastAPI Comparison
Industry-standard async framework with built-in validation and docs. Useful for:
- "Is FastOpenAPI competitive with FastAPI?"
- Understanding the cost of convenience features

## Notes

- All tests use in-memory storage (no database)
- Tests measure framework overhead, not I/O performance
- Results vary based on hardware and system load
- Async frameworks may show different characteristics under different concurrency levels
- Django runs in single-threaded mode (`--nothreading`) for fair comparison
