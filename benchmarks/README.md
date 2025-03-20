## 📊 Quick & Dirty Benchmarks

This benchmark compares the performance of two API implementations:  
- **Original**: Uses standard routing with Pydantic validation.  
- **FastOpenAPI**: Uses proxy routing with Pydantic validation.

Each implementation runs in a separate instance, and the benchmark measures response times across multiple endpoints.

### 📈 Rough results
- You can check rough results here:
  - [Falcon](falcon/FALCON.md)
  - [Flask](flask/FLASK.md)
  - [Quart](quart/QUART.md)
  - [Sanic](sanic/SANIC.md)
  - [Starlette](starlette/STARLETTE.md)
  - [Tornado](tornado/TORNADO.md)

### 📖 How It Works
- The script runs **10,000 requests per endpoint**. You can set your own value.
- It tests **GET, POST, PUT, PATCH, and DELETE** operations.
- For DELETE, it first creates a temporary record to ensure valid deletion.
- Results are printed and compared in a summary table.

### 📂 Benchmark Structure
- The main benchmark script is in `benchmarks/benchmark.py`.
- Test applications are organized in separate folders (`without_fastopenapi/` and `with_fastopenapi/`).
- Each implementation runs on different ports (`8000` and `8001` by default).

### ▶️ Running the Benchmark
1. Start both API implementations:
   ```sh
   python benchmarks/<framework>/without_fastopenapi/run.py
   python benchmarks/<framework>/with_fastopenapi/run.py
   ```
2. Run the benchmark:
   ```sh
   python benchmarks/benchmark.py
   ```
3. Waiting for the results (example):
   ```sh
    Testing Original Implementation
    
    Original - Running 10000 iterations per endpoint
    --------------------------------------------------
    GET all records: 16.3760 sec total, 1.64 ms per request
    GET one record: 17.7782 sec total, 1.78 ms per request
    POST new record: 19.8376 sec total, 1.98 ms per request
    PUT record: 20.4346 sec total, 2.04 ms per request
    PATCH record: 19.7331 sec total, 1.97 ms per request
    DELETE record: 37.4556 sec total, 3.75 ms per request
    
    Testing FastOpenAPI Implementation
    
    FastOpenAPI - Running 10000 iterations per endpoint
    --------------------------------------------------
    GET all records: 17.4752 sec total, 1.75 ms per request
    GET one record: 18.3059 sec total, 1.83 ms per request
    POST new record: 19.9647 sec total, 2.00 ms per request
    PUT record: 19.3761 sec total, 1.94 ms per request
    PATCH record: 19.5880 sec total, 1.96 ms per request
    DELETE record: 40.6837 sec total, 4.07 ms per request
    
    Performance Comparison (10000 iterations)
    ======================================================================
    Endpoint                  Original        FastOpenAPI     Difference     
    ----------------------------------------------------------------------
    GET all records           1.64 ms         1.75 ms         0.11 ms (+6.7%)
    GET one record            1.78 ms         1.83 ms         0.05 ms (+3.0%)
    POST new record           1.98 ms         2.00 ms         0.01 ms (+0.6%)
    PUT record                2.04 ms         1.94 ms         -0.11 ms (-5.2%)
    PATCH record              1.97 ms         1.96 ms         -0.01 ms (-0.7%)
    DELETE record             3.75 ms         4.07 ms         0.32 ms (+8.6%)
   ```
