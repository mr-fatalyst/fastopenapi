
================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1697 | 17.84 |
| `GET one record` | 1807 | 17.43 |
| `POST new record` | 2220 | 13.46 |
| `PUT record` | 2255 | 13.21 |
| `PATCH record` | 2245 | 13.72 |
| `DELETE record` | 3544 | 5.55 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1725 | 17.98 |
| `GET one record` | 1880 | 17.00 |
| `POST new record` | 2240 | 12.87 |
| `PUT record` | 2261 | 12.98 |
| `PATCH record` | 2324 | 12.45 |
| `DELETE record` | 3255 | 6.25 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1906 | 16.49 |
| `GET one record` | 1954 | 15.88 |
| `POST new record` | 2193 | 13.05 |
| `PUT record` | 2105 | 13.82 |
| `PATCH record` | 2214 | 13.39 |
| `DELETE record` | 3347 | 6.49 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 10668 | 1.88 |
| `GET one record` | 9545 | 2.02 |
| `POST new record` | 7331 | 2.64 |
| `PUT record` | 7080 | 2.82 |
| `PATCH record` | 7096 | 2.74 |
| `DELETE record` | 10587 | 1.90 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 1697 | 1725 | +1.6% | 1906 | +12.3% | 10668 | +528.6% |
| `GET one record` | 1807 | 1880 | +4.0% | 1954 | +8.1% | 9545 | +428.1% |
| `POST new record` | 2220 | 2240 | +0.9% | 2193 | -1.2% | 7331 | +230.2% |
| `PUT record` | 2255 | 2261 | +0.3% | 2105 | -6.6% | 7080 | +214.0% |
| `PATCH record` | 2245 | 2324 | +3.5% | 2214 | -1.4% | 7096 | +216.1% |
| `DELETE record` | 3544 | 3255 | -8.2% | 3347 | -5.6% | 10587 | +198.7% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 17.84 | 17.98 | +0.8% | 16.49 | -7.6% | 1.88 | -89.4% |
| `GET one record` | 17.43 | 17.00 | -2.5% | 15.88 | -8.9% | 2.02 | -88.4% |
| `POST new record` | 13.46 | 12.87 | -4.4% | 13.05 | -3.1% | 2.64 | -80.4% |
| `PUT record` | 13.21 | 12.98 | -1.8% | 13.82 | +4.6% | 2.82 | -78.7% |
| `PATCH record` | 13.72 | 12.45 | -9.2% | 13.39 | -2.4% | 2.74 | -80.0% |
| `DELETE record` | 5.55 | 6.25 | +12.6% | 6.49 | +17.0% | 1.90 | -65.8% |

---

[<< Back](../README.md)

---