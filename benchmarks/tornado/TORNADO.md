================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 5829 | 3.63 |
| `GET one record` | 5647 | 3.69 |
| `POST new record` | 5436 | 3.73 |
| `PUT record` | 5513 | 3.72 |
| `PATCH record` | 5561 | 3.75 |
| `DELETE record` | 5632 | 3.81 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 5476 | 3.83 |
| `GET one record` | 5361 | 3.88 |
| `POST new record` | 5189 | 3.99 |
| `PUT record` | 5143 | 3.99 |
| `PATCH record` | 5289 | 3.87 |
| `DELETE record` | 5955 | 3.51 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 4637 | 4.57 |
| `GET one record` | 4161 | 5.04 |
| `POST new record` | 4183 | 4.89 |
| `PUT record` | 3915 | 5.28 |
| `PATCH record` | 3979 | 5.17 |
| `DELETE record` | 4519 | 4.59 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11711 | 1.82 |
| `GET one record` | 10003 | 2.01 |
| `POST new record` | 7729 | 2.54 |
| `PUT record` | 7393 | 2.65 |
| `PATCH record` | 7336 | 2.68 |
| `DELETE record` | 10957 | 1.91 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 5829 | 5476 | -6.0% | 4637 | -20.4% | 11711 | +100.9% |
| `GET one record` | 5647 | 5361 | -5.1% | 4161 | -26.3% | 10003 | +77.1% |
| `POST new record` | 5436 | 5189 | -4.6% | 4183 | -23.1% | 7729 | +42.2% |
| `PUT record` | 5513 | 5143 | -6.7% | 3915 | -29.0% | 7393 | +34.1% |
| `PATCH record` | 5561 | 5289 | -4.9% | 3979 | -28.5% | 7336 | +31.9% |
| `DELETE record` | 5632 | 5955 | +5.7% | 4519 | -19.8% | 10957 | +94.6% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 3.63 | 3.83 | +5.6% | 4.57 | +26.1% | 1.82 | -49.8% |
| `GET one record` | 3.69 | 3.88 | +5.0% | 5.04 | +36.4% | 2.01 | -45.7% |
| `POST new record` | 3.73 | 3.99 | +7.0% | 4.89 | +31.3% | 2.54 | -31.7% |
| `PUT record` | 3.72 | 3.99 | +7.1% | 5.28 | +41.8% | 2.65 | -28.9% |
| `PATCH record` | 3.75 | 3.87 | +3.2% | 5.17 | +37.6% | 2.68 | -28.6% |
| `DELETE record` | 3.81 | 3.51 | -7.9% | 4.59 | +20.6% | 1.91 | -49.8% |

---

[<< Back](../README.md)

---