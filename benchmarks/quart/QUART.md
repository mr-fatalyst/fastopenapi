================================================================================

# SUMMARY: Median Results Across All Rounds

================================================================================

## Framework Pure

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 2043 | 10.26 |
| `GET one record` | 1999 | 10.43 |
| `POST new record` | 1944 | 10.80 |
| `PUT record` | 1945 | 10.83 |
| `PATCH record` | 1980 | 10.51 |
| `DELETE record` | 2069 | 10.08 |

## Framework + Validators

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1988 | 10.55 |
| `GET one record` | 1975 | 10.82 |
| `POST new record` | 1944 | 10.78 |
| `PUT record` | 1977 | 10.60 |
| `PATCH record` | 1952 | 10.97 |
| `DELETE record` | 2112 | 9.91 |

## Framework + FastOpenAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 1800 | 11.57 |
| `GET one record` | 1669 | 12.44 |
| `POST new record` | 1634 | 12.72 |
| `PUT record` | 1594 | 13.13 |
| `PATCH record` | 1582 | 13.61 |
| `DELETE record` | 1764 | 11.83 |

## FastAPI

| Endpoint | RPS (median) | p95 (ms) |
|:---------|-------------:|---------:|
| `GET all records` | 11645 | 1.85 |
| `GET one record` | 10093 | 1.97 |
| `POST new record` | 7763 | 2.51 |
| `PUT record` | 7458 | 2.64 |
| `PATCH record` | 7416 | 2.63 |
| `DELETE record` | 10991 | 1.87 |

================================================================================

## Framework — Performance Comparison (Pure = 100% baseline)

### Requests Per Second (higher is better)

| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 2043 | 1988 | -2.7% | 1800 | -11.9% | 11645 | +470.0% |
| `GET one record` | 1999 | 1975 | -1.2% | 1669 | -16.6% | 10093 | +404.8% |
| `POST new record` | 1944 | 1944 | -0.0% | 1634 | -15.9% | 7763 | +299.4% |
| `PUT record` | 1945 | 1977 | +1.6% | 1594 | -18.0% | 7458 | +283.4% |
| `PATCH record` | 1980 | 1952 | -1.4% | 1582 | -20.1% | 7416 | +274.6% |
| `DELETE record` | 2069 | 2112 | +2.0% | 1764 | -14.7% | 10991 | +431.2% |

### p95 Latency (lower is better)

| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |
|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|
| `GET all records` | 10.26 | 10.55 | +2.8% | 11.57 | +12.7% | 1.85 | -82.0% |
| `GET one record` | 10.43 | 10.82 | +3.7% | 12.44 | +19.2% | 1.97 | -81.2% |
| `POST new record` | 10.80 | 10.78 | -0.2% | 12.72 | +17.9% | 2.51 | -76.7% |
| `PUT record` | 10.83 | 10.60 | -2.0% | 13.13 | +21.3% | 2.64 | -75.6% |
| `PATCH record` | 10.51 | 10.97 | +4.4% | 13.61 | +29.5% | 2.63 | -75.0% |
| `DELETE record` | 10.08 | 9.91 | -1.7% | 11.83 | +17.4% | 1.87 | -81.4% |

---

[<< Back](../README.md)

---