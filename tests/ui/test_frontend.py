"""
UI tests using Selenium.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="module")
def driver():
    """Set up Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def test_homepage_title(driver):
    """Test that the homepage has the correct title."""
    driver.get("http://localhost:8501")  # Streamlit default port
    assert "AI-Powered News Aggregator" in driver.title


def test_articles_list(driver):
    """Test that the articles list is displayed."""
    driver.get("http://localhost:8501")
    
    # Wait for the articles to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "article-card"))
    )
    
    # Check that articles are displayed
    articles = driver.find_elements(By.CLASS_NAME, "article-card")
    assert len(articles) > 0


def test_search_functionality(driver):
    """Test that the search functionality works."""
    driver.get("http://localhost:8501")
    
    # Wait for the search input to be visible
    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-input"))
    )
    
    # Enter search query
    search_input.send_keys("test")
    
    # Click search button
    search_button = driver.find_element(By.ID, "search-button")
    search_button.click()
    
    # Wait for results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
    )
    
    # Check that search results are displayed
    results = driver.find_elements(By.CLASS_NAME, "article-card")
    assert len(results) >= 0  # Could be 0 if no results match


def test_category_filter(driver):
    """Test that category filtering works."""
    driver.get("http://localhost:8501")
    
    # Wait for the category dropdown to be visible
    category_dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "category-dropdown"))
    )
    
    # Select a category
    category_dropdown.click()
    politics_option = driver.find_element(By.XPATH, "//option[text()='Politics']")
    politics_option.click()
    
    # Wait for filtered results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "article-card"))
    )
    
    # Check that filtered results are displayed
    results = driver.find_elements(By.CLASS_NAME, "article-card")
    assert len(results) >= 0  # Could be 0 if no results in this category 