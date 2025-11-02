================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 12048 | 1.53 |
| `GET one record` | 11930 | 1.58 |
| `POST new record` | 8645 | 2.03 |
| `PUT record` | 8795 | 2.03 |
| `PATCH record` | 8829 | 2.03 |
| `DELETE record` | 11361 | 1.64 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11844 | 1.60 |
| `GET one record` | 11786 | 1.60 |
| `POST new record` | 8352 | 2.10 |
| `PUT record` | 8548 | 2.09 |
| `PATCH record` | 8554 | 2.08 |
| `DELETE record` | 11244 | 1.67 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11048 | 1.76 |
| `GET one record` | 9434 | 2.17 |
| `POST new record` | 7877 | 2.43 |
| `PUT record` | 7391 | 2.80 |
| `PATCH record` | 7325 | 2.81 |
| `DELETE record` | 9697 | 2.11 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11656 | 1.71 |
| `GET one record` | 9963 | 1.94 |
| `POST new record` | 7752 | 2.45 |
| `PUT record` | 7423 | 2.69 |
| `PATCH record` | 7359 | 2.63 |
| `DELETE record` | 10989 | 1.80 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 12048 | 11844 | -1.7% | 11048 | -8.3% | 11656 | -3.3% |
| `GET one record` | 11930 | 11786 | -1.2% | 9434 | -20.9% | 9963 | -16.5% |
| `POST new record` | 8645 | 8352 | -3.4% | 7877 | -8.9% | 7752 | -10.3% |
| `PUT record` | 8795 | 8548 | -2.8% | 7391 | -16.0% | 7423 | -15.6% |
| `PATCH record` | 8829 | 8554 | -3.1% | 7325 | -17.0% | 7359 | -16.6% |
| `DELETE record` | 11361 | 11244 | -1.0% | 9697 | -14.6% | 10989 | -3.3% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 1.53 | 1.60 | +4.2% | 1.76 | +15.1% | 1.71 | +11.5% |
| `GET one record` | 1.58 | 1.60 | +1.1% | 2.17 | +37.3% | 1.94 | +22.6% |
| `POST new record` | 2.03 | 2.10 | +3.3% | 2.43 | +20.0% | 2.45 | +20.8% |
| `PUT record` | 2.03 | 2.09 | +2.8% | 2.80 | +38.3% | 2.69 | +32.7% |
| `PATCH record` | 2.03 | 2.08 | +2.5% | 2.81 | +38.9% | 2.63 | +29.5% |
| `DELETE record` | 1.64 | 1.67 | +1.7% | 2.11 | +28.5% | 1.80 | +9.9% |

---

[<< Back](../README.md)

---