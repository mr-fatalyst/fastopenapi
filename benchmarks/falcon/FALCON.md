# Falcon Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.6085 sec total, 0.86 ms per request
GET one record: 8.7683 sec total, 0.88 ms per request
POST new record: 9.1847 sec total, 0.92 ms per request
PUT record: 9.3219 sec total, 0.93 ms per request
PATCH record: 9.1856 sec total, 0.92 ms per request
DELETE record: 17.7793 sec total, 1.78 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.8547 sec total, 0.89 ms per request
GET one record: 9.0380 sec total, 0.90 ms per request
POST new record: 9.5613 sec total, 0.96 ms per request
PUT record: 9.5503 sec total, 0.96 ms per request
PATCH record: 9.4769 sec total, 0.95 ms per request
DELETE record: 18.6130 sec total, 1.86 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint                | Original | FastOpenAPI | Difference      |
|-------------------------|----------|-------------|----------------|
| GET all records         | 0.86 ms  | 0.89 ms     | 0.02 ms (+2.9%) |
| GET one record          | 0.88 ms  | 0.90 ms     | 0.03 ms (+3.1%) |
| POST new record         | 0.92 ms  | 0.96 ms     | 0.04 ms (+4.1%) |
| PUT record              | 0.93 ms  | 0.96 ms     | 0.02 ms (+2.5%) |
| PATCH record            | 0.92 ms  | 0.95 ms     | 0.03 ms (+3.2%) |
| DELETE record           | 1.78 ms  | 1.86 ms     | 0.08 ms (+4.7%) |

---

[<< Back](../README.md)

---