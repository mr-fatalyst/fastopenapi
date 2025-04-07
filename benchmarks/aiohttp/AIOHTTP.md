# AioHttp Benchmark

---

## Testing Original Implementation
```
Original - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.5742 sec total, 0.86 ms per request
GET one record: 8.7001 sec total, 0.87 ms per request
POST new record: 9.0483 sec total, 0.90 ms per request
PUT record: 9.1385 sec total, 0.91 ms per request
PATCH record: 9.1465 sec total, 0.91 ms per request
DELETE record: 17.7022 sec total, 1.77 ms per request
```
---

## Testing FastOpenAPI Implementation

```
FastOpenAPI - Running 10000 iterations per endpoint
--------------------------------------------------
GET all records: 8.7114 sec total, 0.87 ms per request
GET one record: 9.2981 sec total, 0.93 ms per request
POST new record: 9.4486 sec total, 0.94 ms per request
PUT record: 9.4418 sec total, 0.94 ms per request
PATCH record: 9.4253 sec total, 0.94 ms per request
DELETE record: 18.2327 sec total, 1.82 ms per request
```

---

## Performance Comparison (10000 iterations)

| Endpoint         | Original | FastOpenAPI | Difference      |
|------------------|----------|-------------|-----------------|
| GET all records  | 0.86 ms  | 0.87 ms     | +0.01 ms (+1.6%) |
| GET one record   | 0.87 ms  | 0.93 ms     | +0.06 ms (+6.9%) |
| POST new record  | 0.90 ms  | 0.94 ms     | +0.04 ms (+4.4%) |
| PUT record       | 0.91 ms  | 0.94 ms     | +0.03 ms (+3.3%) |
| PATCH record     | 0.91 ms  | 0.94 ms     | +0.03 ms (+3.0%) |
| DELETE record    | 1.77 ms  | 1.82 ms     | +0.05 ms (+3.0%) |



---

[<< Back](../README.md)

---