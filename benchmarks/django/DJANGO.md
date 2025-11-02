================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 2845 | 3.96 |
| `GET one record` | 2794 | 4.18 |
| `POST new record` | 2402 | 4.73 |
| `PUT record` | 2402 | 4.65 |
| `PATCH record` | 2404 | 4.45 |
| `DELETE record` | 2702 | 4.51 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 2745 | 3.81 |
| `GET one record` | 2744 | 3.81 |
| `POST new record` | 2402 | 4.34 |
| `PUT record` | 2371 | 4.39 |
| `PATCH record` | 2404 | 4.55 |
| `DELETE record` | 2898 | 4.69 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1882 | 4.71 |
| `GET one record` | 1841 | 5.11 |
| `POST new record` | 1862 | 5.43 |
| `PUT record` | 1839 | 5.44 |
| `PATCH record` | 1927 | 5.33 |
| `DELETE record` | 2398 | 4.74 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11496 | 1.69 |
| `GET one record` | 9968 | 1.88 |
| `POST new record` | 7740 | 2.46 |
| `PUT record` | 7387 | 2.64 |
| `PATCH record` | 7349 | 2.63 |
| `DELETE record` | 10677 | 1.90 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 2845 | 2745 | -3.5% | 1882 | -33.9% | 11496 | +304.1% |
| `GET one record` | 2794 | 2744 | -1.8% | 1841 | -34.1% | 9968 | +256.8% |
| `POST new record` | 2402 | 2402 | -0.0% | 1862 | -22.5% | 7740 | +222.2% |
| `PUT record` | 2402 | 2371 | -1.3% | 1839 | -23.5% | 7387 | +207.5% |
| `PATCH record` | 2404 | 2404 | +0.0% | 1927 | -19.8% | 7349 | +205.7% |
| `DELETE record` | 2702 | 2898 | +7.3% | 2398 | -11.2% | 10677 | +295.1% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 3.96 | 3.81 | -3.9% | 4.71 | +18.8% | 1.69 | -57.3% |
| `GET one record` | 4.18 | 3.81 | -8.9% | 5.11 | +22.2% | 1.88 | -55.1% |
| `POST new record` | 4.73 | 4.34 | -8.3% | 5.43 | +14.8% | 2.46 | -48.0% |
| `PUT record` | 4.65 | 4.39 | -5.6% | 5.44 | +17.1% | 2.64 | -43.2% |
| `PATCH record` | 4.45 | 4.55 | +2.2% | 5.33 | +19.8% | 2.63 | -40.9% |
| `DELETE record` | 4.51 | 4.69 | +3.9% | 4.74 | +4.9% | 1.90 | -57.9% |

---

[<< Back](../README.md)

---
