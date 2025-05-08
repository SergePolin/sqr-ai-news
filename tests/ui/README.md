# UI Testing with Selenium

This directory contains UI tests for the AI-Powered News Aggregator frontend using Selenium.

## Test Structure

- `test_frontend.py` - Contains the main test cases for the Streamlit UI
- `conftest.py` - Contains the Selenium driver fixture setup

## Test Cases

The tests focus on core functionality:

1. `test_homepage_shows_login` - Verifies that the login/registration form appears on the homepage
2. `test_articles_list` - Tests user registration and login, verifies main content appears
3. `test_search_functionality` - Tests the basic UI elements appear after login
4. `test_category_filter` - Tests that the sidebar appears after login

## Testing Strategy

The tests use a robust approach with multiple selector strategies to handle different UI states:

- Each test attempts to find UI elements using multiple selectors
- The `try_multiple_selectors` helper function tries different approaches to find elements
- Tests include extensive debug logging to help with troubleshooting
- Tests are designed to be resilient to minor UI changes

## Running the Tests

To run the UI tests:

```bash
# Run all UI tests
python -m pytest tests/ui/test_frontend.py

# Run with verbose output
python -m pytest tests/ui/test_frontend.py -v

# Run a specific test
python -m pytest tests/ui/test_frontend.py::test_homepage_shows_login -v
```

Note: The Streamlit application must be running on localhost:8501 before running these tests.

## Troubleshooting

If tests fail:

1. Check browser console for JavaScript errors
2. Look for error messages in the test output (especially lines starting with `[DEBUG]`)
3. Ensure the Streamlit application is running correctly
4. Check that the UI elements haven't changed (selectors may need updating)
5. Increase timeouts if the application is slow to respond

## Further Improvements

Future enhancements could include:

- Capturing screenshots on test failures
- Adding tests for article bookmarking functionality
- Testing user profile management
- Testing error handling scenarios
