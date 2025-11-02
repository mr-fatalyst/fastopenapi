================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11926 | 1.52 |
| `GET one record` | 11900 | 1.53 |
| `POST new record` | 8507 | 2.09 |
| `PUT record` | 8621 | 2.10 |
| `PATCH record` | 8461 | 2.12 |
| `DELETE record` | 10868 | 1.65 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 12009 | 1.56 |
| `GET one record` | 11872 | 1.57 |
| `POST new record` | 8690 | 2.07 |
| `PUT record` | 8993 | 2.04 |
| `PATCH record` | 8876 | 2.04 |
| `DELETE record` | 11266 | 1.57 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11431 | 1.76 |
| `GET one record` | 9566 | 2.02 |
| `POST new record` | 7747 | 2.46 |
| `PUT record` | 7599 | 2.60 |
| `PATCH record` | 7675 | 2.49 |
| `DELETE record` | 10032 | 1.93 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11711 | 1.75 |
| `GET one record` | 10026 | 1.92 |
| `POST new record` | 7720 | 2.49 |
| `PUT record` | 7448 | 2.62 |
| `PATCH record` | 7409 | 2.59 |
| `DELETE record` | 11039 | 1.75 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 11926 | 12009 | +0.7% | 11431 | -4.1% | 11711 | -1.8% |
| `GET one record` | 11900 | 11872 | -0.2% | 9566 | -19.6% | 10026 | -15.8% |
| `POST new record` | 8507 | 8690 | +2.2% | 7747 | -8.9% | 7720 | -9.2% |
| `PUT record` | 8621 | 8993 | +4.3% | 7599 | -11.9% | 7448 | -13.6% |
| `PATCH record` | 8461 | 8876 | +4.9% | 7675 | -9.3% | 7409 | -12.4% |
| `DELETE record` | 10868 | 11266 | +3.7% | 10032 | -7.7% | 11039 | +1.6% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 1.52 | 1.56 | +2.6% | 1.76 | +15.6% | 1.75 | +14.7% |
| `GET one record` | 1.53 | 1.57 | +2.5% | 2.02 | +31.9% | 1.92 | +25.8% |
| `POST new record` | 2.09 | 2.07 | -1.2% | 2.46 | +17.5% | 2.49 | +18.9% |
| `PUT record` | 2.10 | 2.04 | -2.6% | 2.60 | +24.0% | 2.62 | +25.0% |
| `PATCH record` | 2.12 | 2.04 | -3.6% | 2.49 | +17.7% | 2.59 | +22.5% |
| `DELETE record` | 1.65 | 1.57 | -4.8% | 1.93 | +16.8% | 1.75 | +6.1% |

---

[<< Back](../README.md)

---