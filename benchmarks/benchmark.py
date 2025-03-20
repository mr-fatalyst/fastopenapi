import time
import uuid
from typing import Any

import requests


def benchmark_endpoint(method, url, data=None, iterations=100):
    headers = {"Content-Type": "application/json"}
    start = time.time()

    # Special case for DELETE - create a resource first for each iteration
    if method == "DELETE":
        base_url = url.rsplit("/", 1)[0]  # Get the collection URL

        for _ in range(iterations):
            # Create a resource to delete
            record_data = {
                "title": f"Temp Record {uuid.uuid4()}",
                "description": "To be deleted",
                "completed": False,
            }

            create_response = requests.post(base_url, json=record_data, headers=headers)
            if create_response.status_code < 400:
                record_id = create_response.json()["id"]
                delete_url = f"{base_url}/{record_id}"
                requests.delete(delete_url, headers=headers)

    # Regular benchmark for all operations
    elif method == "POST":
        # For POST, create unique items each time
        for _ in range(iterations):
            unique_data = data.copy()
            unique_data["title"] = f"{data['title']} {uuid.uuid4()}"
            requests.post(url, json=unique_data, headers=headers)

    else:
        # For other operations (GET, PUT, PATCH), use standard approach
        for _ in range(iterations):
            if data and method in ["PUT", "PATCH"]:
                requests.request(method, url, json=data, headers=headers)
            else:
                requests.request(method, url, headers=headers)

    duration = time.time() - start
    avg_ms = (duration / iterations) * 1000

    return duration, avg_ms


def run_benchmarks(base_url, label, iterations=100):
    # Create test data
    record_data = {
        "title": "Test Record",
        "description": "This is a test record for benchmarking",
        "completed": False,
    }

    # Create a record to use for single item endpoints
    create_response = requests.post(
        f"{base_url}/records",
        json=record_data,
        headers={"Content-Type": "application/json"},
    )

    record_id = create_response.json()["id"]

    # Define tests to run
    tests = [
        {"name": "GET all records", "method": "GET", "endpoint": "/records"},
        {
            "name": "GET one record",
            "method": "GET",
            "endpoint": f"/records/{record_id}",
        },
        {
            "name": "POST new record",
            "method": "POST",
            "endpoint": "/records",
            "data": record_data,
        },
        {
            "name": "PUT record",
            "method": "PUT",
            "endpoint": f"/records/{record_id}",
            "data": record_data,
        },
        {
            "name": "PATCH record",
            "method": "PATCH",
            "endpoint": f"/records/{record_id}",
            "data": {"title": "Updated Record"},
        },
        {
            "name": "DELETE record",
            "method": "DELETE",
            "endpoint": f"/records/{record_id}",
        },
    ]

    results = {}
    print(f"\n{label} - Running {iterations} iterations per endpoint")
    print("-" * 50)

    for test in tests:
        name = test["name"]
        method = test["method"]
        endpoint = test["endpoint"]
        data = test.get("data")

        url = base_url + endpoint

        try:
            duration, avg_ms = benchmark_endpoint(method, url, data, iterations)
            print(f"{name}: {duration:.4f} sec total, {avg_ms:.2f} ms per request")
            results[name] = {"duration": duration, "avg_ms": avg_ms}
        except Exception as e:
            print(f"{name}: ERROR - {str(e)}")
            results[name] = {"error": str(e)}

    return results


def run_benchmarks_for_apps(apps: list[tuple[str, str]]) -> dict[str, Any]:
    result = {}
    for url, name in apps:
        try:
            print(f"\nTesting {name} Implementation")
            result[name] = run_benchmarks(url, name, iterations)
        except Exception as e:
            print(f"Error testing {name} implementation: {str(e)}")
    return result


def compare_results(results: dict[str, Any]):
    if len(results) == 2:
        print(f"\nPerformance Comparison ({iterations} iterations)")
        print("=" * 70)
        print(
            f"{'Endpoint':<25} {'Original':<15} {'FastOpenAPI':<15} {'Difference':<15}"
        )
        print("-" * 70)

        for endpoint in results["Original"]:
            if endpoint in results["FastOpenAPI"]:
                if (
                    "error" not in results["Original"][endpoint]
                    and "error" not in results["FastOpenAPI"][endpoint]
                ):
                    orig_ms = results["Original"][endpoint]["avg_ms"]
                    fast_ms = results["FastOpenAPI"][endpoint]["avg_ms"]
                    diff = fast_ms - orig_ms
                    diff_percent = (diff / orig_ms) * 100 if orig_ms > 0 else 0

                    print(
                        f"{endpoint:<25} {orig_ms:.2f} ms"
                        f"{'':<8} {fast_ms:.2f} ms"
                        f"{'':<8} {diff:.2f} ms ({diff_percent:+.1f}%)"
                    )
                else:
                    if "error" in results["Original"][endpoint]:
                        print(f"{endpoint:<25} ERROR{'':<16} ", end="")
                        if "error" in results["FastOpenAPI"][endpoint]:
                            print(f"ERROR{'':<16} N/A")
                        else:
                            print(
                                f"{results['FastOpenAPI'][endpoint]['avg_ms']:.2f} ms"
                                f"{'':<8} N/A"
                            )
                    else:
                        print(
                            f"{endpoint:<25} "
                            f"{results['Original'][endpoint]['avg_ms']:.2f} ms"
                            f"{'':<8} ERROR{'':<16} N/A"
                        )


if __name__ == "__main__":
    iterations = 10000
    # Apps for tests
    apps = [
        ("http://localhost:8000", "Original"),
        ("http://localhost:8001", "FastOpenAPI"),
    ]
    # Run benchmarks
    results = run_benchmarks_for_apps(apps)
    # Compare results
    compare_results(results)
