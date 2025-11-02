import asyncio
import gc
import random
import statistics

from benchmarks.common import APIBenchmark, compare_results, print_results
from benchmarks.common.benchmark_base import (
    BenchmarkResult,
    gc_disabled,
    reset_if_available,
)


async def main():
    iterations = 10000
    concurrency = 20
    warmup = 100

    apps = [
        ("http://localhost:8000", "Framework Pure"),
        ("http://localhost:8001", "Framework + Validators"),
        ("http://localhost:8002", "Framework + FastOpenAPI"),
        ("http://localhost:8003", "FastAPI"),
    ]

    rounds = 5
    aggregated: dict[str, list[dict[str, object]]] = {label: [] for _, label in apps}

    for r in range(1, rounds + 1):
        order = apps[:]
        random.shuffle(order)

        print(f"\n{'#' * 80}")
        print(f"# ROUND {r}/{rounds}")
        print(f"{'#' * 80}\n")

        for base_url, label in order:
            print(f"\n> Testing: {label}...")

            await reset_if_available(base_url)
            with gc_disabled():
                benchmark = APIBenchmark(base_url, concurrency=concurrency)
                results = await benchmark.run_full_benchmark(
                    iterations=iterations, warmup=warmup
                )
            print_results(results, f"{label} (round {r})", concurrency)
            aggregated[label].append(results)

            gc.collect()
            await asyncio.sleep(2)

    def summarize(label_results):
        """Calculate median RPS and p95 across all rounds"""
        names = list(label_results[0].keys())
        summary = {}
        for name in names:
            rps_vals = [res[name].rps for res in label_results]
            p95_vals = [res[name].p95 for res in label_results]
            summary[name] = {
                "rps_med": statistics.median(rps_vals),
                "p95_med": statistics.median(p95_vals),
            }
        return summary

    def create_median_results(median_summary):
        """Convert median summary to BenchmarkResult objects for comparison"""
        results = {}
        for endpoint, values in median_summary.items():
            # Create a minimal BenchmarkResult with only needed fields
            result = BenchmarkResult(
                endpoint=endpoint,
                method="",
                duration=0,
                total_requests=0,
                successful=0,
                failed=0,
                rps=values["rps_med"],
                latencies=[values["p95_med"]],  # Use p95 as single latency point
            )
            results[endpoint] = result
        return results

    print("\n" + "=" * 80)
    print("\n# SUMMARY: Median Results Across All Rounds\n")
    print("=" * 80)

    medians = {label: summarize(runs) for label, runs in aggregated.items()}

    for label, items in medians.items():
        print(f"\n## {label}\n")
        print("| Endpoint | RPS (median) | p95 (ms) |")
        print("|:---------|-------------:|---------:|")
        for endpoint, vals in items.items():
            print(f"| `{endpoint}` | {vals['rps_med']:.0f} | {vals['p95_med']:.2f} |")

    # Compare using median values instead of last round
    if all(len(runs) == rounds for runs in aggregated.values()):
        pure_median = create_median_results(medians["Framework Pure"])
        valid_median = create_median_results(medians["Framework + Validators"])
        foapi_median = create_median_results(medians["Framework + FastOpenAPI"])
        fastapi_median = create_median_results(medians["FastAPI"])
        compare_results(
            pure_median, valid_median, foapi_median, fastapi_median, "Framework"
        )


if __name__ == "__main__":
    asyncio.run(main())
