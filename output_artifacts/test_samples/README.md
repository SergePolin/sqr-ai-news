# Test Sample Files 🧪

[![Test Count: 67+](https://img.shields.io/badge/tests-67%2B-blue.svg)](../coverage.xml)
[![Test Types: 6](https://img.shields.io/badge/test%20types-6-blue.svg)](#test-types)
[![Framework: pytest](https://img.shields.io/badge/framework-pytest-blue.svg)](../pytest.ini)

This directory contains examples of the different types of tests implemented in the AI-Powered News Aggregator project, showcasing our comprehensive testing strategy.

## 📝 Table of Contents

- [Test Types](#test-types)
- [Unit Tests](#unit-tests)
- [API Tests](#api-tests)
- [Integration Tests](#integration-tests)
- [UI Tests](#ui-tests)
- [Security Tests](#security-tests)
- [Performance Tests](#performance-tests)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)

## 🔍 Test Types

The project uses a diverse testing approach that covers all layers of the application:

```
Frontend UI ───────┐
                   │
API Endpoints ─────┼──── Test Coverage
                   │
Business Logic ────┤
                   │
Data Access ───────┘
```

## 📋 Unit Tests

Unit tests verify individual components in isolation.

### [`test_crud.py`](test_crud.py)

- Tests CRUD operations for the database layer
- Uses mock DB sessions to isolate database tests
- Verifies all data access functions work correctly

**Key features:**

- Parametrized tests for data variations
- Test fixtures for database setup/teardown
- Complete coverage of CRUD operations

**Example test case:**

```python
def test_get_article(test_db, sample_articles):
    # Test retrieving a specific article works
    article = crud.get_article(test_db, sample_articles[0].id)
    assert article is not None
    assert article.title == "Test Article 1"
```

## 🌐 API Tests

API tests verify that the REST endpoints function correctly.

### [`test_feed.py`](test_feed.py)

- Tests the news feed API endpoints
- Verifies authentication, filtering, and search functionality
- Checks response codes, formats, and data integrity

**Key features:**

- Authentication testing
- Parameterized category filtering tests
- Error condition handling

**Example test case:**

```python
def test_get_articles_with_filter(client, auth_token):
    response = client.get(
        "/api/news/articles/?category=technology",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(article["category"] == "technology" for article in data["articles"])
```

## 🔄 Integration Tests

Integration tests verify that components work together correctly.

### [`test_database_integration.py`](test_database_integration.py)

- Tests database operations with real SQLAlchemy sessions
- Verifies transaction handling and constraints
- Tests database migrations and schema integrity

**Key features:**

- Multi-component transaction tests
- Cascade delete verification
- Foreign key constraint testing

**Example test case:**

```python
def test_user_article_relationship(test_db):
    # Test that user-article relationships work correctly
    user = create_test_user(test_db)
    article = create_test_article(test_db)
    bookmark = add_bookmark(test_db, user.id, article.id)
    
    assert bookmark is not None
    assert bookmark.user_id == user.id
    assert bookmark.article_id == article.id
```

## 🖥️ UI Tests

UI tests verify that the frontend components function correctly.

### [`test_frontend.py`](test_frontend.py)

- Tests UI components using Selenium
- Verifies user flows work end-to-end
- Checks responsive design and UI elements

**Key features:**

- End-to-end user flow testing
- Element visibility and interaction tests
- Form submission verification

**Example test case:**

```python
def test_login_flow(selenium):
    # Test the login flow works correctly
    selenium.get(f"{BASE_URL}/login")
    selenium.find_element(By.ID, "username").send_keys("testuser")
    selenium.find_element(By.ID, "password").send_keys("testpassword")
    selenium.find_element(By.ID, "login-button").click()
    
    # Verify redirect to dashboard
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, "user-dashboard"))
    )
    assert "dashboard" in selenium.current_url
```

## 🔒 Security Tests

Security tests check for vulnerabilities in the codebase.

### [`test_security_bandit.py`](test_security_bandit.py)

- Runs Bandit scanner against the codebase
- Checks for common security issues
- Verifies no critical or high vulnerabilities exist

**Key features:**

- Automated security scanning
- Classification of vulnerabilities by severity
- SAST (Static Application Security Testing)

**Example test case:**

```python
def test_no_critical_vulnerabilities():
    # Run bandit and check for critical vulnerabilities
    result = subprocess.run(["bandit", "-r", "app/", "-f", "json", "-o", "bandit-output.json"])
    
    with open("bandit-output.json") as f:
        report = json.load(f)
        
    # Count critical vulnerabilities
    critical_count = sum(1 for result in report.get("results", []) 
                         if result.get("issue_severity") == "HIGH")
    
    assert critical_count == 0, f"Found {critical_count} critical vulnerabilities"
```

## ⚡ Performance Tests

Performance tests measure API response times under load.

### [`test_api_performance.py`](test_api_performance.py)

- Uses Locust to simulate multiple users
- Measures response times for API endpoints
- Verifies the system handles concurrent requests

**Key features:**

- Concurrent user simulation
- Response time measurement
- Token sharing between users
- Error rate monitoring

**Example configuration:**

```python
class NewsApiUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    @task(3)
    def get_articles(self):
        with self.client.get("/api/news/articles/", catch_response=True) as response:
            assert response.status_code == 200
```

## 🚀 Running Tests

### Running All Tests

```bash
# From project root
pytest

# With coverage
pytest --cov=app --cov-report=term --cov-report=html
```

### Running Specific Test Types

```bash
# Unit tests only
pytest tests/unit/

# API tests only
pytest tests/api/

# UI tests
pytest tests/ui/

# Performance tests (needs separate setup)
cd performance && python test_api_performance.py
```

## 📊 Test Coverage

Current test coverage is 92%, well above the required 60%. View the detailed coverage report in the [htmlcov/](../htmlcov/index.html) directory.

---

*These test samples demonstrate the diversity of testing methods employed in the project, covering all layers of the application from data access to user interface.*
