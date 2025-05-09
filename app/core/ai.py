import logging
import os
from typing import Optional

from openai import AzureOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI configuration
# (update to use only Azure, as per project requirements)
# Expected environment variables:
#   AZURE_OPENAI_ENDPOINT
#   AZURE_OPENAI_API_VERSION
#   AZURE_OPENAI_DEPLOYMENT
#   AZURE_OPENAI_KEY
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.environ.get(
    "AZURE_OPENAI_API_VERSION", "2025-01-01-preview"
)
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# Regular OpenAI configuration (fallback)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

# Initialize OpenAI client
client = None
client_type = None  # 'azure' or 'openai'


def get_openai_client():
    """
    Get the OpenAI client (Azure or regular OpenAI).

    Returns:
        OpenAI client instance or None if not configured
    """
    global client, client_type

    # If client is already initialized, return it
    if client:
        return client

    # Try to initialize Azure OpenAI client
    if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
        try:
            client = AzureOpenAI(
                api_key=AZURE_OPENAI_KEY,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
            )
            client_type = "azure"
            logger.info("Azure OpenAI client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
    else:
        logger.warning(
            "Azure OpenAI credentials missing. Set AZURE_OPENAI_KEY and "
            "AZURE_OPENAI_ENDPOINT."
        )

    # No client could be initialized
    return None


# Initialize the client
client = get_openai_client()

if client is None:
    logger.warning("No OpenAI credentials provided. AI summarization will be disabled.")


def generate_article_summary(content: str, max_length: int = 200) -> Optional[str]:
    """
    Generate a summary of an article using OpenAI.

    Args:
        content: The article content to summarize
        max_length: Maximum length of the summary in characters

    Returns:
        A summary of the article in English or None if summarization fails
    """
    if not client:
        logger.warning("Cannot generate summary: OpenAI client not initialized")
        return None

    if not content or len(content.strip()) < 50:
        logger.warning("Content too short for summarization")
        return None

    try:
        prompt = (
            "Summarize the following news article in a concise summary in English, "
            "regardless of the original language of the article.\n"
            "Keep the summary informative and factual. Maximum length: "
            f"{max_length} characters.\n\n"
            "Article:\n"
            f"{content}\n\n"
            "Summary in English:"
        )

        # Different API calls based on client type
        if client_type == "azure":
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant "
                            "that summarizes news articles in English, "
                            "regardless of the original language."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=150,
                top_p=1.0,
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant "
                            "that summarizes news articles in English, "
                            "regardless of the original language."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=150,
                top_p=1.0,
            )

        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Error generating article summary: {str(e)}")
        # Fallback to simple summary - truncate content with ellipsis
        if content and len(content) > 3:
            # Get the first 150 characters of the content for a simple summary
            simple_summary = content[:150].strip()
            # Add ellipsis if truncated
            if len(content) > 150:
                simple_summary += "..."
            logger.info("Using simple summary as fallback")
            return simple_summary
        return None


def generate_article_category(content: str, title: str) -> Optional[str]:
    """
    Generate a category for an article using OpenAI.

    Args:
        content: The article content
        title: The article title

    Returns:
        A category for the article in English or None if categorization fails
    """
    if not client:
        logger.warning("Cannot generate category: OpenAI client not initialized")
        return None

    if not content or len(content.strip()) < 50:
        logger.warning("Content too short for categorization")
        return None

    try:
        categories = [
            "Politics",
            "Business",
            "Technology",
            "Science",
            "Health",
            "Entertainment",
            "Sports",
            "Environment",
            "Education",
            "Travel",
            "Opinion",
            "Culture",
            "Economy",
            "International",
        ]

        categories_str = ", ".join(categories)

        prompt = (
            "Categorize the following news article into ONE "
            f"of these categories: {categories_str}. "
            "Respond with just the category name in English, nothing else.\n\n"
            f"Title: {title}\n\n"
            "Article:\n"
            f"{content[:1000]}  # Using first 1000 chars for efficiency\n\n"
            "Category in English:"
        )

        # Different API calls based on client type
        if client_type == "azure":
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant "
                            "that categorizes news articles into English categories, "
                            "regardless of the original language."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=20,
                top_p=1.0,
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant "
                            "that categorizes news articles into English categories, "
                            "regardless of the original language."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=20,
                top_p=1.0,
            )

        category = response.choices[0].message.content.strip()

        # Ensure the returned category is in our
        # predefined list (case-insensitive)
        for valid_category in categories:
            if valid_category.lower() == category.lower():
                return valid_category

        # If no match, use the first valid category
        # that contains the returned text
        for valid_category in categories:
            if (
                valid_category.lower() in category.lower()
                or category.lower() in valid_category.lower()
            ):
                return valid_category

        # Fallback to "Other" if no match
        logger.warning(f"Category '{category}' not in predefined list, using 'Other'")
        return "Other"
    except Exception as e:
        logger.error(f"Error generating article category: {str(e)}")
        return None
