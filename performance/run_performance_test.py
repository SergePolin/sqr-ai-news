#!/usr/bin/env python3
"""
Script to run performance tests using Locust in headless mode
and generate a HTML report.
"""

import subprocess
import datetime
import os
import requests
import json
import time
import re
from bs4 import BeautifulSoup

# Create reports directory if it doesn't exist
os.makedirs("tests/performance/reports", exist_ok=True)

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
            "password": "testpassword"
        }
        register_response = requests.post(f"{host}/auth/register", json=user_data)
        
        if register_response.status_code == 201:
            print("Test user created successfully.")
        elif register_response.status_code == 400:
            print("Test user already exists.")
        else:
            print(f"Failed to create test user. Status code: {register_response.status_code}")
            if hasattr(register_response, 'text'):
                print(f"Response: {register_response.text}")
        
        # Verify authentication works
        credentials = {"username": "testuser", "password": "testpassword"}
        login_response = requests.post(f"{host}/auth/login", data=credentials)
        
        if login_response.status_code == 200:
            print("Authentication successful.")
        else:
            print(f"Authentication failed. Status code: {login_response.status_code}")
            if hasattr(login_response, 'text'):
                print(f"Response: {login_response.text}")
    
    except Exception as e:
        print(f"Error setting up test user: {str(e)}")

# Extract data from HTML report
def extract_data_from_report(report_path):
    """Extract performance data from the HTML report."""
    try:
        with open(report_path, 'r') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract metrics
        data = {}
        
        # Get total requests
        stats_div = soup.select_one('div.statistics')
        if stats_div:
            total_requests_match = re.search(r'(\d+) requests', stats_div.text)
            if total_requests_match:
                data['total_requests'] = int(total_requests_match.group(1))
            
            rps_match = re.search(r'(\d+\.?\d*) requests/s', stats_div.text)
            if rps_match:
                data['requests_per_second'] = float(rps_match.group(1))
                
            failures_match = re.search(r'(\d+) failures', stats_div.text)
            if failures_match:
                data['failures'] = int(failures_match.group(1))
        
        # Extract endpoint data
        endpoints = {}
        tables = soup.select('table.stats')
        if tables:
            for row in tables[0].select('tr')[1:]:  # Skip header row
                cols = row.select('td')
                if len(cols) >= 7:
                    name = cols[1].text.strip()
                    if name != 'Aggregated':
                        median = float(cols[4].text.strip())
                        p95 = float(cols[5].text.strip())
                        endpoints[name] = {'median': median, 'p95': p95}
        
        data['endpoints'] = endpoints
        return data
    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        return None

# Setup test user before running performance tests
setup_test_user()

print(f"Starting performance test against {host}...")
print(f"Report will be saved to: tests/performance/reports/{filename}")

# Run Locust test
result = subprocess.run([
    "locust",
    "-f", "tests/performance/test_api_performance.py",
    "--headless",
    "--host", host,
    "-u", "50",  # Number of users
    "-r", "10",  # Spawn rate (users per second)
    "--run-time", "30s",
    "--html", f"./tests/performance/reports/{filename}"
], check=False)

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
            f.write(f"## Test Configuration\n")
            f.write(f"- **Users**: 50\n")
            f.write(f"- **Spawn Rate**: 10 users/second\n")
            f.write(f"- **Run Time**: 30 seconds\n")
            f.write(f"- **Host**: {host}\n\n")
            
            if data:
                f.write(f"## Performance Results\n\n")
                f.write(f"- **Total Requests**: {data.get('total_requests', 'N/A')}\n")
                f.write(f"- **Requests Per Second**: {data.get('requests_per_second', 'N/A')}\n")
                f.write(f"- **Failed Requests**: {data.get('failures', 'N/A')}\n\n")
                
                f.write(f"## Endpoint Performance\n\n")
                f.write(f"| Endpoint | Median Response Time (ms) | 95th Percentile (ms) |\n")
                f.write(f"|---------|----------------------------|------------------------|\n")
                
                endpoints = data.get('endpoints', {})
                for name, metrics in endpoints.items():
                    f.write(f"| {name} | {metrics.get('median', 'N/A')} | {metrics.get('p95', 'N/A')} |\n")
                
                # Check performance against requirements
                f.write(f"\n## Quality Requirements Assessment\n\n")
                
                # Check if any endpoint exceeds 200ms response time
                exceeds_limit = any(metrics.get('median', 0) > 200 for metrics in endpoints.values())
                if exceeds_limit:
                    f.write("❌ **Response Time Requirement**: Some endpoints exceed the 200ms median response time requirement.\n\n")
                    f.write("| Endpoint | Response Time (ms) | Status |\n")
                    f.write("|---------|-------------------|--------|\n")
                    for name, metrics in endpoints.items():
                        status = "❌ Exceeds limit" if metrics.get('median', 0) > 200 else "✅ Within limit"
                        f.write(f"| {name} | {metrics.get('median', 'N/A')} | {status} |\n")
                else:
                    f.write("✅ **Response Time Requirement**: All endpoints meet the 200ms median response time requirement.\n")
                    
                # Check for any failures
                if data.get('failures', 0) > 0:
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