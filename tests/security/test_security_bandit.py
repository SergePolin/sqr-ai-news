"""
Security tests using Bandit.

To run:
1. Install bandit: pip install bandit
2. Run: python -m tests.security.test_security_bandit
"""
import subprocess
import os
import sys
import json
from datetime import datetime


def run_bandit_scan():
    """Run bandit security scan on the codebase."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)

    json_report_path = os.path.join(
        report_dir, f"bandit_report_{timestamp}.json")
    html_report_path = os.path.join(
        report_dir, f"bandit_report_{timestamp}.html")

    # Run bandit scan with JSON output
    print("Running Bandit security scan...")
    cmd = [
        "bandit",
        "-r",
        "app",  # scan the app directory
        "-f", "json",
        "-o", json_report_path,
        "-c", "bandit.yaml",  # Optional: use a custom config file
        "-ll",  # Report only high and medium severity issues
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Bandit scan completed. Report saved to {json_report_path}")
    except subprocess.CalledProcessError as e:
        print(f"Bandit scan failed with error code {e.returncode}")
        return False

    # Generate HTML report
    cmd = [
        "bandit",
        "-r",
        "app",  # scan the app directory
        "-f", "html",
        "-o", html_report_path,
        "-c", "bandit.yaml",  # Optional: use a custom config file
        "-ll",  # Report only high and medium severity issues
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"HTML report generated at {html_report_path}")
    except subprocess.CalledProcessError:
        print("Failed to generate HTML report")

    # Parse JSON report to check for critical issues
    try:
        with open(json_report_path, 'r') as f:
            report_data = json.load(f)

        # Check for high severity issues
        high_severity_issues = [
            result for result in report_data.get('results', [])
            if result.get('issue_severity') == 'HIGH'
        ]

        if high_severity_issues:
            print(
                f"WARNING: {len(high_severity_issues)} "
                "high severity issues found!"
            )
            for issue in high_severity_issues:
                print(
                    f"- {issue.get('filename')}:{issue.get('line_number')} - "
                    f"{issue.get('issue_text')}"
                )
            return False
        else:
            print("No high severity issues found.")
            return True
    except Exception as e:
        print(f"Error parsing report: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_bandit_scan()
    sys.exit(0 if success else 1)
