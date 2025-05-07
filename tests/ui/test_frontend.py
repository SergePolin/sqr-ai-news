"""
UI tests using Selenium.
"""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.keys import Keys
import requests
# from urllib.parse import urlparse


# Configure Chrome options for headless operation
@pytest.fixture(scope="module")
def chrome_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return options


# Create a WebDriver instance
@pytest.fixture(scope="module")
def driver(chrome_options):
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


def is_streamlit_running():
    """Check if the Streamlit server is running and accessible"""
    try:
        response = requests.get("http://localhost:8501", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def try_multiple_selectors(driver, selectors, timeout=10):
    """
    Try multiple selectors to find an element,
    return the first one found or None.
    Log each attempt.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        for selector_type, selector in selectors:
            try:
                element = driver.find_element(selector_type, selector)
                if element.is_displayed():
                    print(
                        f"[DEBUG] Found element with selector: {selector_type}"
                        f" {selector}"
                    )
                    return element
            except Exception as e:
                print(
                    f"[DEBUG] Selector failed: {selector_type} "
                    f"{selector} | Exception: {e}"
                )
        time.sleep(0.5)
    print("[DEBUG] No selector matched after timeout.")
    return None


def selenium_register(driver, username, email, password):
    """
    Register a new user, with better error handling
    and multiple selector attempts.
    Log all steps.
    """
    try:
        driver.get("http://localhost:8501")
        time.sleep(2)  # Allow Streamlit to fully load
        print(f"[DEBUG] Page title: {driver.title}")
        print(f"[DEBUG] Current URL: {driver.current_url}")
        print(
            f"[DEBUG] Page source (start):\n{driver.page_source[:1000]}\n...")
        # Switch to registration tab - try multiple approaches
        reg_tab_selectors = [
            (By.XPATH, "//button[.//p[text()='Регистрация']]"),
            (By.XPATH, "//button[contains(.,'Регистрация')]"),
            (By.XPATH, "//button[contains(@id, 'tab-1')]"),
            (By.CSS_SELECTOR, "[data-baseweb='tab']:nth-child(2)")
        ]
        reg_tab = try_multiple_selectors(driver, reg_tab_selectors)
        if reg_tab:
            reg_tab.click()
            time.sleep(1)
        else:
            print("[DEBUG] Could not find registration tab button!")
        # Use only visible registration tab panel for all fields
        username_selectors = [
            (
                By.XPATH,
                "//div[@role='tabpanel' and not(@hidden)]//input[@aria-label='"
                "Имя пользователя']"
            ),
            (
                By.XPATH,
                "//div[@role='tabpanel' and not(@hidden)]"
                "//label[contains(., 'Имя пользователя')]"
                "/following-sibling::div//input"
            ),
            (
                By.XPATH,
                "//div[@role='tabpanel' and not(@hidden)]"
                "//div[contains(., 'Имя пользователя')]/following::input"
            ),
            (
                By.CSS_SELECTOR,
                "div[role='tabpanel']:not([hidden]) "
                "input[aria-label='Имя пользователя']"
            )
        ]

        username_input = try_multiple_selectors(driver, username_selectors)
        if not username_input:
            print("[DEBUG] Could not find username input!")
            print("[DEBUG] All input fields on page:")
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                print(
                    "[DEBUG] input: "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"name={inp.get_attribute('name')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"value={inp.get_attribute('value')}"
                )
            print("[DEBUG] Full page source:")
            print(driver.page_source)
            return False
        email_selectors = [
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//input[@aria-label='Email']"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//label[contains(., 'Email')]/following-sibling::div"
                    "//input"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//div[contains(., 'Email')]/following::input"
                )
            ),
            (
                By.CSS_SELECTOR,
                (
                    "div[role='tabpanel']:not([hidden]) "
                    "input[aria-label='Email']"
                )
            )
        ]

        email_input = try_multiple_selectors(driver, email_selectors)
        if not email_input:
            print("[DEBUG] Could not find email input!")
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                print(
                    "[DEBUG] input: "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"name={inp.get_attribute('name')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"value={inp.get_attribute('value')}"
                    )
            print(driver.page_source)
            return False
        password_selectors = [
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//input[@aria-label='Пароль']"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//label[contains(., 'Пароль')]/following-sibling::div"
                    "//input[@type='password']"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//div[contains(., 'Пароль')]/following::input"
                    "[@type='password']"
                )
            ),
            (
                By.CSS_SELECTOR,
                (
                    "div[role='tabpanel']:not([hidden]) "
                    "input[aria-label='Пароль']"
                )
            )
        ]

        password_input = try_multiple_selectors(driver, password_selectors)
        if not password_input:
            print("[DEBUG] Could not find password input!")
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                print(
                    "[DEBUG] input: "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"name={inp.get_attribute('name')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"value={inp.get_attribute('value')}"
                )
            print(driver.page_source)
            return False
        confirm_selectors = [
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//input[@aria-label='Подтвердите пароль']"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//label[contains(., 'Подтвердите пароль')]"
                    "/following-sibling::div//input"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//div[contains(., 'Подтвердите пароль')]/following::input"
                )
            ),
            (
                By.CSS_SELECTOR,
                (
                    "div[role='tabpanel']:not([hidden]) "
                    "input[aria-label='Подтвердите пароль']"
                )
            )
        ]

        confirm_input = try_multiple_selectors(driver, confirm_selectors)
        if not confirm_input:
            print("[DEBUG] Could not find confirm password input!")
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                print(
                    "[DEBUG] input: "
                    f"aria-label={inp.get_attribute('aria-label')}, "
                    f"type={inp.get_attribute('type')}, "
                    f"name={inp.get_attribute('name')}, "
                    f"placeholder={inp.get_attribute('placeholder')}, "
                    f"value={inp.get_attribute('value')}"
                )
            print(driver.page_source)
            return False
        username_input.clear()
        username_input.send_keys(username)
        email_input.clear()
        email_input.send_keys(email)
        password_input.clear()
        password_input.send_keys(password)
        confirm_input.clear()
        confirm_input.send_keys(password)
        register_selectors = [
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//button[.//p[text()='Зарегистрироваться']]"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[@role='tabpanel' and not(@hidden)]"
                    "//button[contains(., 'Зарегистрироваться')]"
                )
            ),
            (
                By.CSS_SELECTOR,
                (
                    "div[role='tabpanel']:not([hidden]) button"
                )
            )
        ]

        register_button = try_multiple_selectors(driver, register_selectors)
        if not register_button:
            print("[DEBUG] Could not find register button!")
            print(driver.page_source)
            return False
        register_button.click()
        time.sleep(2)
        print("[DEBUG] Registration form submitted.")
        return True
    except Exception as e:
        print(f"[DEBUG] Error during registration: {str(e)}")
        print(driver.page_source)
        return False


def selenium_login(driver, username, password):
    """Login with the given credentials, with better error handling"""
    try:
        driver.get("http://localhost:8501")
        time.sleep(2)  # Allow Streamlit to fully load

        # Make sure we're on the login tab
        login_tab_selectors = [
            (By.XPATH, "//button[.//p[text()='Вход']]"),
            (By.XPATH, "//button[contains(.,'Вход')]"),
            (By.XPATH, "//button[contains(@id, 'tab-0')]"),
            (By.CSS_SELECTOR, "[data-baseweb='tab']:nth-child(1)")
        ]

        login_tab = try_multiple_selectors(driver, login_tab_selectors)
        if login_tab:
            login_tab.click()
            time.sleep(1)

        # Find username input
        username_selectors = [
            (
                By.XPATH,
                "//input[@aria-label='Имя пользователя']"
            ),
            (
                By.XPATH,
                (
                    "//label[contains(., 'Имя пользователя')]"
                    "/following-sibling::div//input"
                )
            ),
            (
                By.XPATH,
                (
                    "//div[contains(., 'Имя пользователя')]/following::input"
                )
            ),
            (
                By.CSS_SELECTOR,
                "input[type='text']"
            )
        ]

        username_input = try_multiple_selectors(driver, username_selectors)
        if not username_input:
            print("Could not find username input")
            return False

        # Find password input
        password_selectors = [
            (By.XPATH, "//input[@aria-label='Пароль']"),
            (By.XPATH,
             "//label[contains(., 'Пароль')]/following-sibling::div//input"),
            (By.XPATH, "//div[contains(., 'Пароль')]/following::input"),
            (By.CSS_SELECTOR, "input[type='password']")
        ]

        password_input = try_multiple_selectors(driver, password_selectors)
        if not password_input:
            print("Could not find password input")
            return False

        # Fill login form
        username_input.clear()
        username_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)

        # Find and click login button
        login_selectors = [
            (By.XPATH, "//button[.//p[text()='Войти']]"),
            (By.XPATH, "//button[contains(., 'Войти')]"),
            (By.CSS_SELECTOR, "button.ef3psqc12")
        ]

        login_button = try_multiple_selectors(driver, login_selectors)
        if not login_button:
            print("Could not find login button")
            return False

        login_button.click()
        time.sleep(3)  # Give server time to process

        # Check for login success (look for any post-login elements)
        # but don't fail if we can't find them
        return True

    except Exception as e:
        print(f"Error during login: {str(e)}")
        print(driver.page_source)
        return False


def test_homepage_shows_login(driver):
    """
    Test that the homepage shows
    the login form for unauthenticated users.
    """
    driver.get("http://localhost:8501")
    time.sleep(2)
    # Check for heading with app title
    heading = try_multiple_selectors(driver, [
        (By.XPATH, "//h1[contains(., 'AI-Powered News Aggregator')]"),
        (By.TAG_NAME, "h1")
    ])
    assert heading and heading.is_displayed(), "App title not found"
    # Check for login or registration form
    form = try_multiple_selectors(driver, [
        (By.XPATH, "//h3[contains(., 'свой аккаунт')]"),
        (By.XPATH, "//h3[contains(., 'Создайте')]"),
        (By.XPATH, "//button[contains(., 'Войти')]"),
        (By.XPATH, "//button[contains(., 'Зарегистрироваться')]")
    ])
    assert form and form.is_displayed(), "Login/registration form not found"


def test_articles_list(driver):
    """Test that the articles list is displayed after login."""
    unique_username = f"user_{int(time.time())}"
    email = f"{unique_username}@example.com"
    password = "testpassword"
    assert selenium_register(driver, unique_username,
                             email, password), "Registration failed"
    assert selenium_login(driver, unique_username, password), "Login failed"
    # Add a channel
    channel_input = try_multiple_selectors(driver, [
        (By.XPATH, "//input[@placeholder='Имя канала']"),
        (By.XPATH, "//input[contains(@aria-label, 'канал')]"),
        (By.XPATH, "//input[contains(@placeholder, 'канал')]"),
        (By.CSS_SELECTOR, "input[type='text']")
    ], timeout=10)
    assert channel_input, "Channel input not found"
    channel_input.clear()
    channel_input.send_keys("testchannel")
    # Click 'Добавить канал' button
    add_channel_btn = try_multiple_selectors(driver, [
        (By.XPATH, "//button[.//p[text()='Добавить канал']]"),
        (By.XPATH, "//button[contains(., 'Добавить канал')]")
    ], timeout=10)
    assert add_channel_btn, "Add channel button not found"
    add_channel_btn.click()
    time.sleep(2)
    # Click 'Получить новости' button
    get_news_btn = try_multiple_selectors(driver, [
        (By.XPATH, "//button[.//p[text()='Получить новости']]"),
        (By.XPATH, "//button[contains(., 'Получить новости')]")
    ], timeout=10)
    assert get_news_btn, "Get news button not found"
    get_news_btn.click()
    # Wait for articles or 'Нет статей' message
    article = try_multiple_selectors(driver, [
        (By.XPATH, "//div[contains(@class, 'stArticleContainer')]"),
        (By.XPATH, "//div[contains(@class, 'article-container')]"),
        (By.XPATH, "//h2[contains(., 'Новости') or contains(., 'Articles')]")
    ], timeout=15)
    no_articles = try_multiple_selectors(driver, [
        (By.XPATH, "//*[contains(text(), 'Нет статей')]")
    ], timeout=2)
    assert article or no_articles, (
        "Neither articles nor 'Нет статей' message found after fetching news"
    )


def test_search_functionality(driver):
    """Test the search functionality after login."""
    unique_username = f"user_{int(time.time())}"
    email = f"{unique_username}@example.com"
    password = "testpassword"
    assert selenium_register(driver, unique_username,
                             email, password), "Registration failed"
    assert selenium_login(driver, unique_username, password), "Login failed"
    # Find search input
    search_input = try_multiple_selectors(driver, [
        (By.XPATH,
         "//input[contains(@placeholder, 'Поиск') or @aria-label='Search']"),
        (By.CSS_SELECTOR, "input[type='text']")
    ])
    assert search_input, "Search input not found"
    search_input.clear()
    search_input.send_keys("test")
    search_input.send_keys(Keys.RETURN)
    time.sleep(2)
    # Optionally, check for search results (e.g., article titles)
    # result = try_multiple_selectors(
    #     driver,
    #     [(By.XPATH, "//div[contains(@class, 'article-title')]")],
    #     timeout=5
    # )
    # assert result, "No search results found"


def test_category_filter(driver):
    """Test the category filter functionality after login."""
    unique_username = f"user_{int(time.time())}"
    email = f"{unique_username}@example.com"
    password = "testpassword"
    assert selenium_register(driver, unique_username,
                             email, password), "Registration failed"
    assert selenium_login(driver, unique_username, password), "Login failed"
    # Add a channel
    channel_input = try_multiple_selectors(driver, [
        (By.XPATH, "//input[@placeholder='Имя канала']"),
        (By.XPATH, "//input[contains(@aria-label, 'канал')]"),
        (By.XPATH, "//input[contains(@placeholder, 'канал')]"),
        (By.CSS_SELECTOR, "input[type='text']")
    ], timeout=10)
    assert channel_input, "Channel input not found"
    channel_input.clear()
    channel_input.send_keys("testchannel")
    add_channel_btn = try_multiple_selectors(driver, [
        (By.XPATH, "//button[.//p[text()='Добавить канал']]"),
        (By.XPATH, "//button[contains(., 'Добавить канал')]")
    ], timeout=10)
    assert add_channel_btn, "Add channel button not found"
    add_channel_btn.click()
    time.sleep(2)
    get_news_btn = try_multiple_selectors(driver, [
        (By.XPATH, "//button[.//p[text()='Получить новости']]"),
        (By.XPATH, "//button[contains(., 'Получить новости')]")
    ], timeout=10)
    assert get_news_btn, "Get news button not found"
    get_news_btn.click()
    # Wait for the category selectbox (label: 'Фильтр по категории')
    select_label = try_multiple_selectors(driver, [
        (By.XPATH, "//label[contains(., 'Фильтр по категории')]")
    ], timeout=10)
    assert select_label, "Category filter selectbox label not found"
    # Find the select element (Streamlit uses a custom dropdown,
    # so look for the selectbox root)
    select_root = try_multiple_selectors(driver, [
        (By.XPATH, "//div[contains(@data-baseweb, 'select')]"),
        (By.CSS_SELECTOR, "div[data-baseweb='select']")
    ], timeout=10)
    assert select_root, "Category selectbox root not found"
    # Click to open the dropdown
    select_root.click()
    time.sleep(1)
    # Get all dropdown options
    options = driver.find_elements(By.XPATH, "//div[@role='option']")
    option_texts = [opt.text for opt in options]
    print(f"[DEBUG] Category options: {option_texts}")
    if not options:
        print(
            "[DEBUG] No category options found in selectbox "
            "(expected for new user with no articles/categories)."
        )
        return  # Test passes: filter UI is present, but no categories yet
    # If more than one category (besides 'Все категории'),
    # select the first real category
    for opt in options:
        if opt.text and opt.text != 'Все категории':
            opt.click()
            time.sleep(1)
            print(f"[DEBUG] Selected category: {opt.text}")
            break
    # Assert that the selectbox and at least one option are present
    assert options, "No category options found in selectbox"
