# Remove the unused imports at the top of the file
# import time
# import json
# import pytest
import requests
from locust import HttpUser, between, task, events

# Remove the pytest skip to allow running the test
# pytest.skip("Locust file, skip in pytest collection", allow_module_level=True)
"""
Performance tests using Locust.

To run:
1. Install locust: pip install locust
2. Run locust -f tests/performance/test_api_performance.py
3. Open browser at http://localhost:8089
"""

# Global token cache to share between users
AUTH_TOKENS = {}


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--host", default="http://127.0.0.1:8000")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Test is starting")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test is stopping")


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # Login first to get a token
        response = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "password123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        result = response.json()
        self.token = result.get("access_token")
        print("Logged in and got token")

    @task
    def health_check(self):
        self.client.get("/health")
        print("Health check performed")

    @task
    def get_articles(self):
        self.client.get(
            "/api/news/articles/",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/news/articles/",
        )

    @task
    def get_feed(self):
        self.client.get(
            "/feed/",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/feed/",
        )

    @task
    def search_articles(self):
        search_terms = ["technology", "science", "politics", "sports"]
        for term in search_terms:
            self.client.get(
                f"/api/news/articles/?search={term}",
                headers={"Authorization": f"Bearer {self.token}"},
                name="/api/news/articles/?search=TERM",
            )


class NewsApiUser(HttpUser):
    """Simulated user accessing the news API."""

    # Wait between 1 to 5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Setup before starting tests - load auth token."""
        # Use shared token if available, otherwise authenticate
        if "testuser" in AUTH_TOKENS and AUTH_TOKENS["testuser"]:
            self.token = AUTH_TOKENS["testuser"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            # Fallback authentication if global setup failed
            self._authenticate()

    def _authenticate(self):
        """Authenticate and store token."""
        try:
            credentials = {"username": "testuser", "password": "testpassword"}
            response = self.client.post("/auth/login", data=credentials)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                if self.token:
                    self.client.headers.update(
                        {"Authorization": f"Bearer {self.token}"}
                    )
                    # Cache the token globally
                    AUTH_TOKENS["testuser"] = self.token
        except Exception as e:
            print(f"Authentication error: {str(e)}")

    @task(3)
    def get_articles(self):
        """Test the articles endpoint."""
        with self.client.get("/api/news/articles/", catch_response=True) as response:
            if response.status_code == 401:
                # Re-authenticate on 401
                self._authenticate()
                response.failure("Authentication failed, token refreshed")
            elif response.status_code != 200:
                response.failure(f"Failed with status code: {response.status_code}")

    @task(1)
    def get_article_detail(self):
        """Test the article detail endpoint."""
        # In a real test, you'd get the ID dynamically
        # This is simplified for the template
        article_id = 1
        with self.client.get(
            f"/api/news/articles/{article_id}", catch_response=True
        ) as response:
            if response.status_code == 401:
                # Re-authenticate on 401
                self._authenticate()
                response.failure("Authentication failed, token refreshed")
            elif response.status_code != 200 and response.status_code != 404:
                # 404 is acceptable if article doesn't exist
                response.failure(f"Failed with status code: {response.status_code}")

    @task(2)
    def get_filtered_articles(self):
        """Test filtered articles."""
        categories = ["politics", "technology", "sports", "entertainment"]
        for category in categories:
            with self.client.get(
                f"/api/news/articles/?category={category}", catch_response=True
            ) as response:
                if response.status_code == 401:
                    # Re-authenticate on 401
                    self._authenticate()
                    response.failure("Authentication failed, token refreshed")
                elif response.status_code != 200:
                    response.failure(f"Failed with status code: {response.status_code}")

    @task(1)
    def health_check(self):
        """Test the health check endpoint."""
        self.client.get("/health")


class SearchApiUser(HttpUser):
    """Simulated user searching for articles."""

    wait_time = between(5, 15)

    def on_start(self):
        """Setup before starting tests - load auth token."""
        # Use shared token if available, otherwise authenticate
        if "testuser" in AUTH_TOKENS and AUTH_TOKENS["testuser"]:
            self.token = AUTH_TOKENS["testuser"]
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            # Fallback authentication if global setup failed
            self._authenticate()

    def _authenticate(self):
        """Authenticate and store token."""
        try:
            credentials = {"username": "testuser", "password": "testpassword"}
            response = self.client.post("/auth/login", data=credentials)

            if response.status_code == 200:
                self.token = response.json().get("access_token")
                if self.token:
                    self.client.headers.update(
                        {"Authorization": f"Bearer {self.token}"}
                    )
                    # Cache the token globally
                    AUTH_TOKENS["testuser"] = self.token
        except Exception as e:
            print(f"Authentication error: {str(e)}")

    @task
    def search_articles(self):
        """Test search functionality."""
        search_terms = ["python", "news", "technology", "world"]
        for term in search_terms:
            with self.client.get(
                f"/api/news/articles/?search={term}", catch_response=True
            ) as response:
                if response.status_code == 401:
                    # Re-authenticate on 401
                    self._authenticate()
                    response.failure("Authentication failed, token refreshed")
                elif response.status_code != 200:
                    response.failure(f"Failed with status code: {response.status_code}")


# To generate a test report:
"""
To generate a performance report, run the following after the test:

import subprocess
import datetime

# Generate a unique timestamp for the report name
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"performance_report_{timestamp}.html"

# Export the Locust report
subprocess.run([
    "locust",
    "-f", "tests/performance/test_api_performance.py",
    "--headless",
    "-u", "100",  # Number of users
    "-r", "10",   # Spawn rate (users per second)
    "--run-time", "30s",
    "--html", f"./tests/performance/reports/{filename}"
])
"""
