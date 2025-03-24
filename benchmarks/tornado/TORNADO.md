# Tornado Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 9.3412 sec total, 0.93 ms per request
GET one record: 9.5527 sec total, 0.96 ms per request
POST new record: 9.9068 sec total, 0.99 ms per request
PUT record: 9.8596 sec total, 0.99 ms per request
PATCH record: 9.8612 sec total, 0.99 ms per request
DELETE record: 19.0970 sec total, 1.91 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 9.5980 sec total, 0.96 ms per request
GET one record: 9.9557 sec total, 1.00 ms per request
POST new record: 10.2566 sec total, 1.03 ms per request
PUT record: 10.4081 sec total, 1.04 ms per request
PATCH record: 10.2608 sec total, 1.03 ms per request
DELETE record: 19.9923 sec total, 2.00 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint                 | Original | FastOpenAPI | Difference |
|--------------------------|----------|-------------|------------|
| GET all records          | 0.93 ms  | 0.96 ms     | 0.03 ms (+2.7%)  |
| GET one record           | 0.96 ms  | 1.00 ms     | 0.04 ms (+4.2%)  |
| POST new record          | 0.99 ms  | 1.03 ms     | 0.03 ms (+3.5%)  |
| PUT record               | 0.99 ms  | 1.04 ms     | 0.05 ms (+5.6%)  |
| PATCH record             | 0.99 ms  | 1.03 ms     | 0.04 ms (+4.1%)  |
| DELETE record            | 1.91 ms  | 2.00 ms     | 0.09 ms (+4.7%)  |

---

[<< Back](../README.md)

---