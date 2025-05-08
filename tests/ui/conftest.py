"""
Fixtures for UI testing with Selenium.
"""

import pytest
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture
def base_url():
    """Return the base URL for the frontend application."""
    return "http://localhost:8501"


@pytest.fixture
def wait(driver):
    """Return a WebDriverWait instance for the driver."""
    return WebDriverWait(driver, 10)
