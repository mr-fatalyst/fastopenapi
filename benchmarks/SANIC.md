# Sanic Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.7815 sec total, 0.88 ms per request
GET one record: 9.0136 sec total, 0.90 ms per request
POST new record: 9.4816 sec total, 0.95 ms per request
PUT record: 9.2173 sec total, 0.92 ms per request
PATCH record: 9.2911 sec total, 0.93 ms per request
DELETE record: 18.5361 sec total, 1.85 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 9.0011 sec total, 0.90 ms per request
GET one record: 9.3199 sec total, 0.93 ms per request
POST new record: 9.6575 sec total, 0.97 ms per request
PUT record: 9.6792 sec total, 0.97 ms per request
PATCH record: 9.8153 sec total, 0.98 ms per request
DELETE record: 19.9205 sec total, 1.99 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint                | Original | FastOpenAPI | Difference      |
|-------------------------|----------|-------------|----------------|
| GET all records         | 0.88 ms  | 0.90 ms     | 0.02 ms (+2.5%) |
| GET one record          | 0.90 ms  | 0.93 ms     | 0.03 ms (+3.4%) |
| POST new record         | 0.95 ms  | 0.97 ms     | 0.02 ms (+1.9%) |
| PUT record              | 0.92 ms  | 0.97 ms     | 0.05 ms (+5.0%) |
| PATCH record            | 0.93 ms  | 0.98 ms     | 0.05 ms (+5.6%) |
| DELETE record           | 1.85 ms  | 1.99 ms     | 0.14 ms (+7.5%) |

---

[<< Back](README.md)

---