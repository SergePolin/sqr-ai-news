#!/usr/bin/env python3
"""
Script to run performance tests using Locust in headless mode
and generate a HTML report.
"""

import subprocess
import datetime
import os
import requests
import re
from bs4 import BeautifulSoup
import argparse
import statistics
import sys

# Set up reports directory
REPORT_DIR = "output_artifacts"
os.makedirs(REPORT_DIR, exist_ok=True)

# API endpoint to test
API_URL = "http://localhost:8000"

# Generate a unique timestamp for the report name
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"performance_report_{timestamp}.html"

# Base URL of the API
host = "http://localhost:8000"


# Ensure the test user exists before running tests
def setup_test_user():
    """Create a test user for performance testing."""
    print("Setting up test user for performance testing...")

    # Register test user
    try:
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
        }
        register_response = requests.post(f"{host}/auth/register", json=user_data)

        if register_response.status_code == 201:
            print("Test user created successfully.")
        elif register_response.status_code == 400:
            print("Test user already exists.")
        else:
            print(
                f"Failed to create test user. Status code: {register_response.status_code}"
            )
            if hasattr(register_response, "text"):
                print(f"Response: {register_response.text}")

        # Verify authentication works
        credentials = {"username": "testuser", "password": "testpassword"}
        login_response = requests.post(f"{host}/auth/login", data=credentials)

        if login_response.status_code == 200:
            print("Authentication successful.")
        else:
            print(f"Authentication failed. Status code: {login_response.status_code}")
            if hasattr(login_response, "text"):
                print(f"Response: {login_response.text}")

    except Exception as e:
        print(f"Error setting up test user: {str(e)}")


# Extract data from HTML report
def extract_data_from_report(report_path):
    """Extract performance data from the HTML report."""
    try:
        with open(report_path, "r") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract metrics
        data = {}

        # Get total requests
        stats_div = soup.select_one("div.statistics")
        if stats_div:
            total_requests_match = re.search(r"(\d+) requests", stats_div.text)
            if total_requests_match:
                data["total_requests"] = int(total_requests_match.group(1))

            rps_match = re.search(r"(\d+\.?\d*) requests/s", stats_div.text)
            if rps_match:
                data["requests_per_second"] = float(rps_match.group(1))

            failures_match = re.search(r"(\d+) failures", stats_div.text)
            if failures_match:
                data["failures"] = int(failures_match.group(1))

        # Extract endpoint data
        endpoints = {}
        tables = soup.select("table.stats")
        if tables:
            for row in tables[0].select("tr")[1:]:  # Skip header row
                cols = row.select("td")
                if len(cols) >= 7:
                    name = cols[1].text.strip()
                    if name != "Aggregated":
                        median = float(cols[4].text.strip())
                        p95 = float(cols[5].text.strip())
                        endpoints[name] = {"median": median, "p95": p95}

        data["endpoints"] = endpoints
        return data
    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        return None


# Setup test user before running performance tests
setup_test_user()

print(f"Starting performance test against {host}...")
print(f"Report will be saved to: tests/performance/reports/{filename}")

# Run Locust test
result = subprocess.run(
    [
        "locust",
        "-f",
        "tests/performance/test_api_performance.py",
        "--headless",
        "--host",
        host,
        "-u",
        "50",  # Number of users
        "-r",
        "10",  # Spawn rate (users per second)
        "--run-time",
        "30s",
        "--html",
        f"./tests/performance/reports/{filename}",
    ],
    check=False,
)

if result.returncode == 0:
    print(f"Performance test completed successfully.")
    print(f"Report saved to: tests/performance/reports/{filename}")

    # Print short summary
    print("\nAnalyzing performance results...")

    # Check if the report exists before attempting to analyze it
    report_path = f"./tests/performance/reports/{filename}"
    if os.path.exists(report_path):
        # Extract data from report
        data = extract_data_from_report(report_path)

        # Create a summary markdown file with key findings
        summary_file = "./tests/performance/latest_test_summary.md"
        with open(summary_file, "w") as f:
            f.write(f"# Performance Test Summary - {timestamp}\n\n")
            f.write("## Test Configuration\n")
            f.write("- **Users**: 50\n")
            f.write("- **Spawn Rate**: 10 users/second\n")
            f.write("- **Run Time**: 30 seconds\n")
            f.write(f"- **Host**: {host}\n\n")

            if data:
                f.write("## Performance Results\n\n")
                f.write(f"- **Total Requests**: {data.get('total_requests', 'N/A')}\n")
                f.write(f"- **Requests Per Second**: {data.get('requests_per_second', 'N/A')}\n")
                f.write(f"- **Failed Requests**: {data.get('failures', 'N/A')}\n\n")

                f.write("## Endpoint Performance\n\n")
                f.write("| Endpoint | Median Response Time (ms) | 95th Percentile (ms) |\n")
                f.write("|---------|----------------------------|------------------------|\n")

                endpoints = data.get("endpoints", {})
                for name, metrics in endpoints.items():
                    f.write(
                        f"| {name} | {metrics.get('median', 'N/A')} | {metrics.get('p95', 'N/A')} |\n"
                    )

                # Check performance against requirements
                f.write("\n## Quality Requirements Assessment\n\n")

                # Check if any endpoint exceeds 200ms response time
                exceeds_limit = any(
                    metrics.get("median", 0) > 200 for metrics in endpoints.values()
                )
                if exceeds_limit:
                    f.write(
                        "❌ **Response Time Requirement**: Some endpoints exceed the 200ms median response time requirement.\n\n"
                    )
                    f.write("| Endpoint | Response Time (ms) | Status |\n")
                    f.write("|---------|-------------------|--------|\n")
                    for name, metrics in endpoints.items():
                        status = (
                            "❌ Exceeds limit"
                            if metrics.get("median", 0) > 200
                            else "✅ Within limit"
                        )
                        f.write(
                            f"| {name} | {metrics.get('median', 'N/A')} | {status} |\n"
                        )
                else:
                    f.write(
                        "✅ **Response Time Requirement**: All endpoints meet the 200ms median response time requirement.\n"
                    )

                # Check for any failures
                if data.get("failures", 0) > 0:
                    f.write("\n❌ **Reliability**: Test contains failed requests.\n")
                else:
                    f.write("\n✅ **Reliability**: No failed requests detected.\n")

            f.write(f"\nSee full report at: [HTML Report](./reports/{filename})\n")

        print(f"Summary written to: {summary_file}")
        print(f"Full report path: ./tests/performance/reports/{filename}")
    else:
        print("Warning: Report file was not generated.")
else:
    print(f"Performance test failed with exit code: {result.returncode}")

def run_tests():
    """Run performance tests and output reports."""
    parser = argparse.ArgumentParser(description="Run performance tests for the News Aggregator API")
    parser.add_argument("--host", default="http://localhost:8000", help="API host to test")
    parser.add_argument("--users", type=int, default=10, help="Number of users to simulate")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    parser.add_argument("--output", default="output_artifacts", help="Output directory for reports")
    args = parser.parse_args()

    # Verify API is running
    try:
        response = requests.get(f"{args.host}/health", timeout=5)
        if response.status_code != 200:
            print(f"API not ready: Status code {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False

    print(f"API is running. Starting performance test with {args.users} users for {args.duration} seconds")

    # Run Locust headless
    cmd = [
        "locust",
        "-f", "performance/test_api_performance.py",
        "--host", args.host,
        "--users", str(args.users),
        "--spawn-rate", str(args.users),
        "--run-time", f"{args.duration}s",
        "--headless",
        "--csv", f"{args.output}/performance"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Performance test completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Locust: {e}")
        return False


class PerformanceReport:
    """Generate performance reports from test results."""

    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = self._load_data()

    def _load_data(self):
        """Load data from CSV file."""
        import csv
        data = []
        try:
            with open(f"{self.csv_file}_stats.csv", 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            print(f"Error loading CSV data: {e}")
            return []

    def generate_report(self, output_dir="output_artifacts"):
        """Generate performance report."""
        if not self.data:
            print("No data to generate report from")
            return False

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{output_dir}/performance_report_{timestamp}.md"

        # Calculate key metrics
        response_times = []
        failures = 0
        requests = 0

        for entry in self.data:
            if entry["Name"] != "Aggregated":
                # Skip non-aggregated data
                continue

            failures += int(entry.get("Failures", 0))
            requests += int(entry.get("Requests", 0))
            
            # Get response times
            rt_50 = float(entry.get("50%", 0))
            rt_95 = float(entry.get("95%", 0))
            rt_99 = float(entry.get("99%", 0))
            rt_max = float(entry.get("Max", 0))
            
            response_times = [rt_50, rt_95, rt_99, rt_max]

        # Calculate failure rate safely
        failure_rate = (failures / requests) * 100 if requests > 0 else 0.00
        
        # Generate report content
        report_content = [
            "# Performance Test Report",
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"Total Requests: {requests}",
            f"Failed Requests: {failures}",
            f"Failure Rate: {failure_rate:.2f}%",
            "",
            "## Response Times (ms)",
            f"Median (50%): {rt_50:.2f}",
            f"95th Percentile: {rt_95:.2f}",
            f"99th Percentile: {rt_99:.2f}",
            f"Maximum: {rt_max:.2f}",
            f"Average: {statistics.mean(response_times):.2f}",
            "",
            "## Performance Evaluation",
            f"API Performance: {'✅ PASSED' if rt_95 < 200 else '❌ FAILED'}",
            f"Target: 95% of requests complete within 200ms",
            f"Actual: 95% of requests complete within {rt_95:.2f}ms",
            "",
            "## Detailed Results",
            "See the CSV files in the output directory for detailed results."
        ]

        # Write report to file
        try:
            os.makedirs(output_dir, exist_ok=True)
            with open(report_file, 'w') as f:
                f.write('\n'.join(report_content))
            print(f"Performance report generated: {report_file}")
            return True
        except Exception as e:
            print(f"Error writing performance report: {e}")
            return False


if __name__ == "__main__":
    success = run_tests()
    if success:
        report = PerformanceReport("output_artifacts/performance")
        report.generate_report()
    sys.exit(0 if success else 1)
