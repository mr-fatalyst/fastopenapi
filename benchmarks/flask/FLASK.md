# Flask Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 12.3051 sec total, 1.23 ms per request
GET one record: 12.5205 sec total, 1.25 ms per request
POST new record: 13.2638 sec total, 1.33 ms per request
PUT record: 13.3373 sec total, 1.33 ms per request
PATCH record: 13.1245 sec total, 1.31 ms per request
DELETE record: 25.7178 sec total, 2.57 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 12.7424 sec total, 1.27 ms per request
GET one record: 13.0017 sec total, 1.30 ms per request
POST new record: 13.5450 sec total, 1.35 ms per request
PUT record: 13.5281 sec total, 1.35 ms per request
PATCH record: 13.5548 sec total, 1.36 ms per request
DELETE record: 26.7906 sec total, 2.68 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint                | Original | FastOpenAPI | Difference      |
|-------------------------|----------|-------------|----------------|
| GET all records         | 1.23 ms  | 1.27 ms     | 0.04 ms (+3.6%) |
| GET one record          | 1.25 ms  | 1.30 ms     | 0.05 ms (+3.8%) |
| POST new record         | 1.33 ms  | 1.35 ms     | 0.03 ms (+2.1%) |
| PUT record              | 1.33 ms  | 1.35 ms     | 0.02 ms (+1.4%) |
| PATCH record            | 1.31 ms  | 1.36 ms     | 0.04 ms (+3.3%) |
| DELETE record           | 2.57 ms  | 2.68 ms     | 0.11 ms (+4.2%) |

---

[<< Back](README.md)

---