from openai import AzureOpenAI, OpenAI
import os
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI configuration (update to use only Azure, as per project requirements)
# Expected environment variables:
#   AZURE_OPENAI_ENDPOINT
#   AZURE_OPENAI_API_VERSION
#   AZURE_OPENAI_DEPLOYMENT
#   AZURE_OPENAI_KEY
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

# Regular OpenAI configuration (fallback)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

# Initialize OpenAI client
client = None
client_type = None  # 'azure' or 'openai'

# Only use Azure OpenAI
if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        client_type = 'azure'
        logger.info("Azure OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        client = None
else:
    logger.warning("Azure OpenAI credentials missing. Set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT.")

if client is None:
    logger.warning("No OpenAI credentials provided. AI summarization will be disabled.")

def generate_article_summary(content: str, max_length: int = 200) -> Optional[str]:
    """
    Generate a summary of an article using OpenAI.
    
    Args:
        content: The article content to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        A summary of the article or None if summarization fails
    """
    if not client:
        logger.warning("Cannot generate summary: OpenAI client not initialized")
        return None
        
    if not content or len(content.strip()) < 50:
        logger.warning("Content too short for summarization")
        return None
        
    try:
        prompt = f"""Summarize the following news article in a concise summary.
        Keep the summary informative and factual. Maximum length: {max_length} characters.
        
        Article:
        {content}
        
        Summary:"""
        
        # Different API calls based on client type
        if client_type == 'azure':
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150,
                top_p=1.0
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150,
                top_p=1.0
            )
        
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Error generating article summary: {str(e)}")
        return None 

def generate_article_category(content: str, title: str) -> Optional[str]:
    """
    Generate a category for an article using OpenAI.
    
    Args:
        content: The article content
        title: The article title
        
    Returns:
        A category for the article or None if categorization fails
    """
    if not client:
        logger.warning("Cannot generate category: OpenAI client not initialized")
        return None
        
    if not content or len(content.strip()) < 50:
        logger.warning("Content too short for categorization")
        return None
        
    try:
        categories = [
            "Politics", "Business", "Technology", "Science", "Health", 
            "Entertainment", "Sports", "Environment", "Education", 
            "Travel", "Opinion", "Culture", "Economy", "International"
        ]
        
        categories_str = ", ".join(categories)
        
        prompt = f"""Categorize the following news article into ONE of these categories: {categories_str}.
        Respond with just the category name, nothing else.
        
        Title: {title}
        
        Article:
        {content[:1000]}  # Using first 1000 chars for efficiency
        
        Category:"""
        
        # Different API calls based on client type
        if client_type == 'azure':
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes news articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=20,
                top_p=1.0
            )
        else:  # OpenAI
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that categorizes news articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=20,
                top_p=1.0
            )
        
        category = response.choices[0].message.content.strip()
        
        # Ensure the returned category is in our predefined list (case-insensitive)
        for valid_category in categories:
            if valid_category.lower() == category.lower():
                return valid_category
                
        # If no match, use the first valid category that contains the returned text
        for valid_category in categories:
            if valid_category.lower() in category.lower() or category.lower() in valid_category.lower():
                return valid_category
                
        # Fallback to "Other" if no match
        logger.warning(f"Category '{category}' not in predefined list, using 'Other'")
        return "Other"
    except Exception as e:
        logger.error(f"Error generating article category: {str(e)}")
        return None 