# Django Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 16.6954 sec total, 1.67 ms per request
GET one record: 17.9311 sec total, 1.79 ms per request
POST new record: 17.9401 sec total, 1.79 ms per request
PUT record: 17.6793 sec total, 1.77 ms per request
PATCH record: 17.6725 sec total, 1.77 ms per request
DELETE record: 38.5721 sec total, 3.86 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 21.4920 sec total, 2.15 ms per request
GET one record: 20.1516 sec total, 2.02 ms per request
POST new record: 20.0375 sec total, 2.00 ms per request
PUT record: 22.2360 sec total, 2.22 ms per request
PATCH record: 21.9553 sec total, 2.20 ms per request
DELETE record: 40.2411 sec total, 4.02 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint                | Original | FastOpenAPI | Difference       |
|-------------------------|----------|-------------|------------------|
| GET all records         | 1.67 ms  | 2.15 ms     | 0.48 ms (+28.7%) |
| GET one record          | 1.79 ms  | 2.02 ms     | 0.22 ms (+12.4%) |
| POST new record         | 1.79 ms  | 2.00 ms     | 0.21 ms (+11.7%) |
| PUT record              | 1.77 ms  | 2.22 ms     | 0.46 ms (+25.8%) |
| PATCH record            | 1.77 ms  | 2.20 ms     | 0.43 ms (+24.2%) |
| DELETE record           | 3.86 ms  | 4.02 ms     | 0.17 ms (+4.3%)  |

---

[<< Back](../README.md)

---
