# Starlette Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.6688 sec total, 0.87 ms per request
GET one record: 8.9452 sec total, 0.89 ms per request
POST new record: 9.2628 sec total, 0.93 ms per request
PUT record: 9.2470 sec total, 0.92 ms per request
PATCH record: 9.3018 sec total, 0.93 ms per request
DELETE record: 20.9903 sec total, 2.10 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 9.2649 sec total, 0.93 ms per request
GET one record: 9.2726 sec total, 0.93 ms per request
POST new record: 9.7103 sec total, 0.97 ms per request
PUT record: 9.7489 sec total, 0.97 ms per request
PATCH record: 9.6531 sec total, 0.97 ms per request
DELETE record: 21.9329 sec total, 2.19 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint               | Original | FastOpenAPI | Difference      |
|------------------------|----------|-------------|----------------|
| GET all records        | 0.87 ms  | 0.93 ms     | 0.06 ms (+6.9%) |
| GET one record         | 0.89 ms  | 0.93 ms     | 0.03 ms (+3.7%) |
| POST new record        | 0.93 ms  | 0.97 ms     | 0.04 ms (+4.8%) |
| PUT record             | 0.92 ms  | 0.97 ms     | 0.05 ms (+5.4%) |
| PATCH record           | 0.93 ms  | 0.97 ms     | 0.04 ms (+3.8%) |
| DELETE record          | 2.10 ms  | 2.19 ms     | 0.09 ms (+4.5%) |


---

[<< Back](../README.md)

---