================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 12198 | 1.43 |
| `GET one record` | 12149 | 1.42 |
| `POST new record` | 8296 | 2.12 |
| `PUT record` | 8364 | 2.15 |
| `PATCH record` | 8295 | 2.21 |
| `DELETE record` | 11057 | 1.61 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11708 | 1.52 |
| `GET one record` | 12088 | 1.42 |
| `POST new record` | 8163 | 2.23 |
| `PUT record` | 8518 | 2.13 |
| `PATCH record` | 8537 | 2.09 |
| `DELETE record` | 11295 | 1.55 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 12104 | 1.58 |
| `GET one record` | 11987 | 1.65 |
| `POST new record` | 8595 | 2.10 |
| `PUT record` | 8898 | 2.18 |
| `PATCH record` | 8960 | 2.17 |
| `DELETE record` | 8758 | 2.30 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11616 | 1.80 |
| `GET one record` | 9993 | 1.91 |
| `POST new record` | 7729 | 2.45 |
| `PUT record` | 7381 | 2.63 |
| `PATCH record` | 7240 | 2.69 |
| `DELETE record` | 10950 | 1.77 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 12198 | 11708 | -4.0% | 12104 | -0.8% | 11616 | -4.8% |
| `GET one record` | 12149 | 12088 | -0.5% | 11987 | -1.3% | 9993 | -17.7% |
| `POST new record` | 8296 | 8163 | -1.6% | 8595 | +3.6% | 7729 | -6.8% |
| `PUT record` | 8364 | 8518 | +1.8% | 8898 | +6.4% | 7381 | -11.7% |
| `PATCH record` | 8295 | 8537 | +2.9% | 8960 | +8.0% | 7240 | -12.7% |
| `DELETE record` | 11057 | 11295 | +2.1% | 8758 | -20.8% | 10950 | -1.0% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 1.43 | 1.52 | +5.9% | 1.58 | +10.2% | 1.80 | +25.6% |
| `GET one record` | 1.42 | 1.42 | -0.1% | 1.65 | +16.2% | 1.91 | +34.8% |
| `POST new record` | 2.12 | 2.23 | +5.1% | 2.10 | -1.0% | 2.45 | +15.6% |
| `PUT record` | 2.15 | 2.13 | -0.8% | 2.18 | +1.6% | 2.63 | +22.2% |
| `PATCH record` | 2.21 | 2.09 | -5.1% | 2.17 | -1.7% | 2.69 | +22.2% |
| `DELETE record` | 1.61 | 1.55 | -3.8% | 2.30 | +42.6% | 1.77 | +9.8% |

---

[<< Back](../README.md)

---