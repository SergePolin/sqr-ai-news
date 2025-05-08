import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from app.core.ai import (client, client_type, generate_article_category,
                         generate_article_summary)

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Sample test data
SAMPLE_ARTICLE = """
Scientists have discovered a new species of deep-sea fish that can survive 
extreme pressure. The fish, named Pseudoliparis swirei, was found in the Mariana Trench
at depths of up to 8,000 meters. The discovery could help researchers understand
how organisms adapt to extreme conditions. The study was published in the journal
Nature Ecology & Evolution.
"""

SAMPLE_TITLE = "New Deep-Sea Fish Discovered in Mariana Trench"


@pytest.fixture
def mock_azure_client():
    """Create a mock for the Azure OpenAI client."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "This is a mock summary."
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    logger.debug("Created mock Azure client")
    return mock_client


@pytest.fixture
def setup_env():
    """Set up environment variables for testing."""
    original_values = {}
    # Save original values
    for key in ["AZURE_OPENAI_KEY", "AZURE_OPENAI_ENDPOINT"]:
        original_values[key] = os.environ.get(key)
        os.environ[key] = "test_value"

    logger.debug("Set environment variables for testing")
    yield

    # Restore original values
    for key, value in original_values.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value
    logger.debug("Restored original environment variables")


@patch("app.core.ai.client")
def test_generate_article_summary_success(mock_client):
    """Test successful article summary generation."""
    # Setup mock
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Scientists discovered a new deep-sea fish that can survive extreme pressure in the Mariana Trench."
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    logger.debug("Mock client configured for successful summary generation")

    # Call function
    summary = generate_article_summary(SAMPLE_ARTICLE)

    logger.debug(f"Generated summary: {summary}")

    # Assertions
    assert (
        summary
        == "Scientists discovered a new deep-sea fish that can survive extreme pressure in the Mariana Trench."
    )
    mock_client.chat.completions.create.assert_called_once()
    logger.debug("Summary generation test passed")


@patch("app.core.ai.client")
def test_generate_article_summary_no_client(mock_client):
    """Test summary generation when client is None."""
    # Setup mock - make client None to test this case
    mock_client.__bool__.return_value = False  # Make client evaluate to False
    logger.debug("Mock client configured to evaluate to False")

    # Call function with the mock
    summary = generate_article_summary(SAMPLE_ARTICLE)

    logger.debug(f"Result with no client: {summary}")

    # Assertions
    assert summary is None
    logger.debug("No client test passed")


@patch("app.core.ai.client")
def test_generate_article_summary_empty_content(mock_client):
    """Test summary generation with empty content."""
    logger.debug("Testing summary generation with empty content")

    # Call function with empty content
    summary = generate_article_summary("")

    logger.debug(f"Result with empty content: {summary}")

    # Assertions
    assert summary is None
    mock_client.chat.completions.create.assert_not_called()
    logger.debug("Empty content test passed")


@patch("app.core.ai.client")
def test_generate_article_summary_exception(mock_client):
    """Test summary generation with an exception."""
    # Setup mock to raise exception
    exception_message = "API Error"
    mock_client.chat.completions.create.side_effect = Exception(exception_message)
    logger.debug(f"Mock client configured to raise exception: {exception_message}")

    # Call function
    summary = generate_article_summary(SAMPLE_ARTICLE)

    logger.debug(f"Result with exception: {summary}")

    # Assertions
    assert summary is None
    mock_client.chat.completions.create.assert_called_once()
    logger.debug("Exception handling test passed")


@patch("app.core.ai.client")
def test_generate_article_category_success(mock_client):
    """Test successful article category generation."""
    # Setup mock
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Science"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    # Call function
    category = generate_article_category(SAMPLE_ARTICLE, SAMPLE_TITLE)

    # Assertions
    assert category == "Science"
    mock_client.chat.completions.create.assert_called_once()


@patch("app.core.ai.client")
def test_generate_article_category_no_client(mock_client):
    """Test category generation when client is None."""
    # Setup mock
    mock_client.return_value = None

    # Call function
    category = generate_article_category(SAMPLE_ARTICLE, SAMPLE_TITLE)

    # Assertions
    assert category is None


@patch("app.core.ai.client")
def test_generate_article_category_empty_content(mock_client):
    """Test category generation with empty content."""
    # Call function with empty content
    category = generate_article_category("", SAMPLE_TITLE)

    # Assertions
    assert category is None
    mock_client.chat.completions.create.assert_not_called()


@patch("app.core.ai.client")
def test_generate_article_category_exception(mock_client):
    """Test category generation with an exception."""
    # Setup mock to raise exception
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    # Call function
    category = generate_article_category(SAMPLE_ARTICLE, SAMPLE_TITLE)

    # Assertions
    assert category is None
    mock_client.chat.completions.create.assert_called_once()


def test_client_initialization_with_valid_credentials(setup_env):
    """Test client initialization with valid credentials."""
    logger.debug("Testing client initialization with valid credentials")

    with patch("app.core.ai.AzureOpenAI") as mock_azure:
        mock_client = MagicMock()
        mock_azure.return_value = mock_client
        logger.debug("Mocked AzureOpenAI client")

        # Re-import the module to trigger initialization
        import importlib

        import app.core.ai

        importlib.reload(app.core.ai)
        logger.debug("Reloaded app.core.ai module")

        # Check if client is initialized correctly
        logger.debug(f"Client value: {app.core.ai.client}")
        logger.debug(f"Client type: {app.core.ai.client_type}")

        assert app.core.ai.client is not None
        assert app.core.ai.client_type == "azure"
        logger.debug("Client initialization test passed")
