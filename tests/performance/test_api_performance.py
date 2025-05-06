import pytest; pytest.skip('Locust file, skip in pytest collection', allow_module_level=True)
"""
Performance tests using Locust.

To run:
1. Install locust: pip install locust
2. Run locust -f tests/performance/test_api_performance.py
3. Open browser at http://localhost:8089
"""
import time
from locust import HttpUser, task, between


class NewsApiUser(HttpUser):
    """Simulated user accessing the news API."""
    
    # Wait between 1 to 5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """Setup before starting tests."""
        # Add any setup code here (e.g., login if needed)
        pass
    
    @task(3)
    def get_articles(self):
        """Test the articles endpoint."""
        self.client.get("/api/news/articles/")
    
    @task(1)
    def get_article_detail(self):
        """Test the article detail endpoint."""
        # In a real test, you'd get the ID dynamically
        # This is simplified for the template
        article_id = 1
        self.client.get(f"/api/news/articles/{article_id}")
    
    @task(2)
    def get_filtered_articles(self):
        """Test filtered articles."""
        categories = ["politics", "technology", "sports", "entertainment"]
        for category in categories:
            self.client.get(f"/api/news/articles/?category={category}")
    
    @task(1)
    def health_check(self):
        """Test the health check endpoint."""
        self.client.get("/health")


class SearchApiUser(HttpUser):
    """Simulated user searching for articles."""
    
    wait_time = between(5, 15)
    
    @task
    def search_articles(self):
        """Test search functionality."""
        search_terms = ["python", "news", "technology", "world"]
        for term in search_terms:
            self.client.get(f"/api/news/articles/?search={term}")


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