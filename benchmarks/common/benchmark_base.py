import asyncio
import gc
import statistics
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass

import aiohttp


@contextmanager
def gc_disabled():
    was_enabled = gc.isenabled()
    try:
        gc.collect()
        if was_enabled:
            gc.disable()
        yield
    finally:
        if was_enabled:
            gc.enable()
        gc.collect()


@dataclass
class BenchmarkResult:
    endpoint: str
    method: str
    duration: float
    total_requests: int
    successful: int
    failed: int
    rps: float
    latencies: list[float]

    @property
    def p50(self) -> float:
        return self.latencies[len(self.latencies) // 2] if self.latencies else 0

    @property
    def p95(self) -> float:
        return self.latencies[int(len(self.latencies) * 0.95)] if self.latencies else 0

    @property
    def p99(self) -> float:
        return self.latencies[int(len(self.latencies) * 0.99)] if self.latencies else 0

    @property
    def mean(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0

    @property
    def min_lat(self) -> float:
        return min(self.latencies) if self.latencies else 0

    @property
    def max_lat(self) -> float:
        return max(self.latencies) if self.latencies else 0


class APIBenchmark:
    def __init__(self, base_url: str, concurrency: int = 100):
        self.base_url = base_url
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

    async def make_request(
        self, session: aiohttp.ClientSession, method: str, url: str, data: dict = None
    ) -> tuple[float, bool]:
        """Make single request and return (latency_ms, success)"""
        async with self.semaphore:
            start = time.perf_counter()
            try:
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    await resp.read()
                    success = resp.status < 400
                    latency = (time.perf_counter() - start) * 1000
                    return latency, success
            except Exception:
                latency = (time.perf_counter() - start) * 1000
                return latency, False

    async def benchmark_endpoint(
        self,
        method: str,
        endpoint: str,
        data: dict = None,
        iterations: int = 10000,
        warmup: int = 100,
    ) -> BenchmarkResult:
        """Benchmark single endpoint"""
        url = f"{self.base_url}{endpoint}"
        latencies = []
        successful = 0
        failed = 0

        async with aiohttp.ClientSession() as session:
            # Warm-up phase
            warmup_tasks = [
                self.make_request(session, method, url, data) for _ in range(warmup)
            ]
            await asyncio.gather(*warmup_tasks)

            # Actual benchmark
            start = time.perf_counter()

            # Special handling for POST - unique data each time
            if method == "POST":
                tasks = []
                for _ in range(iterations):
                    unique_data = data.copy()
                    unique_data["title"] = f"{data['title']} {uuid.uuid4()}"
                    tasks.append(self.make_request(session, method, url, unique_data))
            else:
                tasks = [
                    self.make_request(session, method, url, data)
                    for _ in range(iterations)
                ]

            results = await asyncio.gather(*tasks)
            duration = time.perf_counter() - start

            # Process results
            for latency, success in results:
                latencies.append(latency)
                if success:
                    successful += 1
                else:
                    failed += 1

            latencies.sort()

        return BenchmarkResult(
            endpoint=endpoint,
            method=method,
            duration=duration,
            total_requests=iterations,
            successful=successful,
            failed=failed,
            rps=iterations / duration,
            latencies=latencies,
        )

    async def _warmup_delete(
        self, session: aiohttp.ClientSession, url: str, warmup: int
    ) -> None:
        """Warmup phase for DELETE benchmark"""
        for _ in range(warmup):
            record_data = {
                "title": f"Warmup {uuid.uuid4()}",
                "description": "Warmup",
                "is_completed": False,
            }
            try:
                async with session.post(
                    url,
                    json=record_data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status < 400:
                        data = await resp.json()
                        await session.delete(f"{url}/{data['id']}")
            except Exception:
                pass

    async def _create_one_resource(
        self, session: aiohttp.ClientSession, url: str
    ) -> str | None:
        """Create a single resource and return its ID"""
        async with self.semaphore:
            payload = {
                "title": f"Delete Test {uuid.uuid4()}",
                "description": "To be deleted",
                "is_completed": False,
            }
            try:
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status < 400:
                        data = await resp.json()
                        return data.get("id")
                    return None
            except Exception:
                return None

    async def _create_resources_for_delete(
        self, session: aiohttp.ClientSession, url: str, iterations: int
    ) -> list[str]:
        """Create resources for DELETE benchmark and return their IDs"""
        print(f"  Creating {iterations} resources for DELETE test...")

        create_tasks = [
            asyncio.create_task(self._create_one_resource(session, url))
            for _ in range(iterations)
        ]

        record_ids: list[str] = []
        for coro in asyncio.as_completed(create_tasks):
            rid = await coro
            if rid:
                record_ids.append(rid)

        print(f"  Created {len(record_ids)} resources, starting DELETE benchmark...")
        return record_ids

    async def benchmark_delete(
        self, iterations: int = 10000, warmup: int = 100
    ) -> BenchmarkResult:
        """
        Special benchmark for DELETE - creates resources first
        (bounded concurrency & safe I/O)
        """
        url = f"{self.base_url}/records"
        latencies: list[float] = []
        successful = 0
        failed = 0

        connector = aiohttp.TCPConnector(limit=0)

        async with aiohttp.ClientSession(connector=connector) as session:
            # Warmup phase
            await self._warmup_delete(session, url, warmup)

            # Create resources
            record_ids = await self._create_resources_for_delete(
                session, url, iterations
            )

            # Benchmark DELETE operations
            start = time.perf_counter()
            delete_tasks = [
                self.make_request(session, "DELETE", f"{url}/{rid}")
                for rid in record_ids
            ]
            results = await asyncio.gather(*delete_tasks)
            duration = time.perf_counter() - start

            # Process results
            for latency, success in results:
                latencies.append(latency)
                if success:
                    successful += 1
                else:
                    failed += 1

            latencies.sort()

        return BenchmarkResult(
            endpoint="/records/{id}",
            method="DELETE",
            duration=duration,
            total_requests=len(record_ids),
            successful=successful,
            failed=failed,
            rps=len(record_ids) / duration if record_ids else 0.0,
            latencies=latencies,
        )

    async def run_full_benchmark(
        self, iterations: int = 10000, warmup: int = 100
    ) -> dict[str, BenchmarkResult]:
        """Run complete benchmark suite"""
        async with aiohttp.ClientSession() as session:
            record_data = {
                "title": "Test Record",
                "description": "For GET/PUT/PATCH tests",
                "is_completed": False,
            }
            async with session.post(
                f"{self.base_url}/records",
                json=record_data,
                headers={"Content-Type": "application/json"},
            ) as resp:
                data = await resp.json()
                record_id = data["id"]

        tests = [
            ("GET all records", "GET", "/records", None),
            ("GET one record", "GET", f"/records/{record_id}", None),
            (
                "POST new record",
                "POST",
                "/records",
                {
                    "title": "Benchmark Record",
                    "description": "Created during benchmark",
                    "is_completed": False,
                },
            ),
            (
                "PUT record",
                "PUT",
                f"/records/{record_id}",
                {
                    "title": "Updated Record",
                    "description": "Updated during benchmark",
                    "is_completed": True,
                },
            ),
            (
                "PATCH record",
                "PATCH",
                f"/records/{record_id}",
                {"title": "Patched Record"},
            ),
        ]

        results = {}

        for i, (name, method, endpoint, data) in enumerate(tests, 1):
            print(f"  [{i}/{len(tests)}] Benchmarking: {name}...")
            result = await self.benchmark_endpoint(
                method, endpoint, data, iterations, warmup
            )
            results[name] = result

        print(f"  [{len(tests) + 1}/{len(tests) + 1}] Benchmarking: DELETE record...")
        results["DELETE record"] = await self.benchmark_delete(iterations, warmup)

        return results


async def reset_if_available(base_url: str):
    try:
        conn = aiohttp.TCPConnector(limit=0)
        async with aiohttp.ClientSession(connector=conn) as s:
            async with s.post(f"{base_url}/__reset") as resp:
                await resp.read()
    except Exception:
        pass


def print_results(results: dict[str, BenchmarkResult], label: str, concurrency: int):
    print(f"\n{'=' * 80}")
    print(f"\n## {label}")
    print(f"Concurrency: **{concurrency}**\n")

    print(
        "| Endpoint | RPS | Mean (ms) | p50 (ms) | p95 (ms) | "
        "p99 (ms) | Min (ms) | Max (ms) |"
    )
    print(
        "|:---------|----:|----------:|---------:|---------:|"
        "---------:|---------:|---------:|"
    )

    failed_logs: list[str] = []

    for name, result in results.items():
        print(
            f"| `{name}` | "
            f"{result.rps:.0f} | "
            f"{result.mean:.2f} | "
            f"{result.p50:.2f} | "
            f"{result.p95:.2f} | "
            f"{result.p99:.2f} | "
            f"{result.min_lat:.2f} | "
            f"{result.max_lat:.2f} |"
        )
        if result.failed > 0:
            failed_logs.append(
                f"Failed requests: **{result.failed}/{result.total_requests}** "
                f"for `{name}`"
            )

    if failed_logs:
        print("\n> ⚠️ " + "\n> ".join(failed_logs))


def compare_results(
    pure_results: dict[str, BenchmarkResult],
    validators_results: dict[str, BenchmarkResult],
    fastopenapi_results: dict[str, BenchmarkResult],
    fastapi_results: dict[str, BenchmarkResult],
    framework_name: str,
):
    def safe_get(d: dict[str, BenchmarkResult], name: str, attr: str):
        obj = d.get(name)
        return getattr(obj, attr) if obj is not None else None

    def fmt_num(x, digits=0):
        if x is None:
            return "—"
        return f"{x:.{digits}f}" if digits else f"{x:.0f}"

    def pct_change(new, base):
        if new is None or base in (None, 0):
            return None
        return (new / base - 1) * 100

    def fmt_pct(p):
        if p is None:
            return "—"
        sign = "+" if p >= 0 else ""
        return f"{sign}{p:.1f}%"

    # Header
    print(f"\n{'=' * 80}")
    print(f"\n## {framework_name} — Performance Comparison (Pure = 100% baseline)\n")

    # ---------- RPS ----------
    print("### Requests Per Second (higher is better)\n")
    print("| Endpoint | Pure | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |")
    print("|---------|-----:|------------:|---:|-------------:|---:|--------:|---:|")

    for name in pure_results:
        pure_rps = safe_get(pure_results, name, "rps")
        val_rps = safe_get(validators_results, name, "rps")
        fo_rps = safe_get(fastopenapi_results, name, "rps")
        fa_rps = safe_get(fastapi_results, name, "rps")

        print(
            f"| `{name}` | "
            f"{fmt_num(pure_rps)} | "
            f"{fmt_num(val_rps)} | "
            f"{fmt_pct(pct_change(val_rps, pure_rps))} | "
            f"{fmt_num(fo_rps)} | "
            f"{fmt_pct(pct_change(fo_rps, pure_rps))} | "
            f"{fmt_num(fa_rps)} | "
            f"{fmt_pct(pct_change(fa_rps, pure_rps))} |"
        )

    # ---------- p95 Latency ----------
    print("\n### p95 Latency (lower is better)\n")
    print(
        "| Endpoint | Pure (ms) | +Validators | Δ% | +FastOpenAPI | Δ% | FastAPI | Δ% |"
    )
    print(
        "|---------|----------:|------------:|---:|-------------:|---:|--------:|---:|"
    )

    for name in pure_results:
        pure_lat = safe_get(pure_results, name, "p95")
        val_lat = safe_get(validators_results, name, "p95")
        fo_lat = safe_get(fastopenapi_results, name, "p95")
        fa_lat = safe_get(fastapi_results, name, "p95")

        print(
            f"| `{name}` | "
            f"{fmt_num(pure_lat, 2)} | "
            f"{fmt_num(val_lat, 2)} | "
            f"{fmt_pct(pct_change(val_lat, pure_lat))} | "
            f"{fmt_num(fo_lat, 2)} | "
            f"{fmt_pct(pct_change(fo_lat, pure_lat))} | "
            f"{fmt_num(fa_lat, 2)} | "
            f"{fmt_pct(pct_change(fa_lat, pure_lat))} |"
        )
