import time
import json
import pytest
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


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Set up shared test resources before test starts."""
    print("Creating test user before performance test starts...")

    # Use requests directly instead of environment.runner.locust.client
    host = environment.host
    if not host:
        print("Warning: No host specified, using default http://localhost:8000")
        host = "http://localhost:8000"

    try:
        # Create test user
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
        }
        response = requests.post(f"{host}/auth/register", json=user_data)
        print(f"User registration status: {response.status_code}")

        # Get auth token and store in global cache
        credentials = {"username": "testuser", "password": "testpassword"}
        response = requests.post(f"{host}/auth/login", data=credentials)
        if response.status_code == 200:
            AUTH_TOKENS["testuser"] = response.json().get("access_token")
            print(f"Authentication successful, token cached")
        else:
            print(f"Authentication failed: {response.status_code}")
    except Exception as e:
        print(f"Setup failed: {str(e)}")


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
            else:
                # Create test user if it doesn't exist
                user_data = {
                    "username": "testuser",
                    "email": "testuser@example.com",
                    "password": "testpassword",
                }
                self.client.post("/auth/register", json=user_data)
                # Try login again
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
