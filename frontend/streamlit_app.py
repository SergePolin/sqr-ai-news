import streamlit as st
import requests
import re
import os
from bs4 import BeautifulSoup

# import html
import time

# Get API URL from environment or use default
API_URL = os.environ.get("API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 5  # seconds; protects UI from hanging if backend is slow/offline
# Authentication functions


def register_user(username, email, password):
    """Register a new user and return `requests.Response` or None if backend is unreachable."""
    payload = {"username": username, "email": email, "password": password}
    try:
        response = requests.post(
            f"{API_URL}/auth/register", json=payload, timeout=REQUEST_TIMEOUT
        )
        return response
    except requests.exceptions.ConnectionError:
        return None


def login_user(username, password):
    """Login and get access token."""
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return response


def add_channel(channel_name, token):
    if not channel_name:
        st.error("Please enter a channel name.")
        return

    if not re.match(r"^[A-Za-z0-9_]+$", channel_name):
        st.error("Channel name must contain only Latin characters, numbers, and '_'")
        return

    response = requests.post(
        f"{API_URL}/feed",
        json={"Channel_alias": f"@{channel_name}"},
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        st.success(f"Channel @{channel_name} added!")
    else:
        st.error(f"Error adding channel: {response.text}")


def clean_html(html_content):
    """Clean HTML content and extract plain text."""
    # Replace HTML tags with appropriate markdown or remove them
    if not html_content:
        return ""

    # Use BeautifulSoup to parse HTML if possible
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()
    except Exception:
        # Fallback to regex replacements if BeautifulSoup fails
        text = re.sub(r"<[^>]*>", "", html_content)
        return text


def get_news(token, generate_summaries=False, generate_categories=False):
    if not token:
        st.error("You are not authorized. Please log in.")
        return []

    # Custom CSS for better styling
    st.markdown(
        """
    <style>
    .article-card {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 20px;
        margin: 15px 0;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .article-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 10px;
        color: #1E3A8A;
    }
    .article-content {
        color: #333;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 15px;
    }
    .read-more-btn {
        display: inline-block;
        padding: 5px 15px;
        background-color: #4361EE;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        font-size: 0.9rem;
        transition: background-color 0.3s;
        margin-right: 10px;
    }
    .read-more-btn:hover {
        background-color: #3730A3;
    }
    .ai-summary {
        background-color: rgba(144, 238, 144, 0.2);
        padding: 12px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 4px solid #2E8B57;
    }
    .ai-summary h5 {
        margin-top: 0;
        color: #2E8B57;
        font-weight: 600;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    response = requests.get(
        f"{API_URL}/feed?generate_summaries={str(generate_summaries).lower()}"
        f"&generate_categories={str(generate_categories).lower()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code == 200:
        data = response.json()
        # For each channel
        for channel in data:
            st.subheader(f"Channel: {channel['channel_alias']}")
            articles = channel.get("articles", [])
            if articles:  # Check if there are articles
                for idx, article in enumerate(articles):
                    # Clean description/content from HTML tags
                    description = clean_html(article.get("description", ""))
                    title = article.get("title", "")
                    link = article.get("link", "#")

                    # Create article card with proper layout
                    with st.container():
                        # Use columns for better layout
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            # Display title
                            st.markdown(f"### {title}")

                            # Display category if available
                            if article.get("category"):
                                st.markdown(f"**Category:** {article.get('category')}")

                            # Display AI summary first if available
                            if article.get("ai_summary"):
                                st.markdown("**AI Summary:**")
                                st.info(article.get("ai_summary"))

                            # Hide full article text in an accordion
                            with st.expander("Show Full Article"):
                                st.markdown(description)

                        with col2:
                            # Add direct link instead of a button
                            st.markdown(
                                f"[Read on Telegram]({link})", unsafe_allow_html=False
                            )

                        # Add separator between articles
                        st.markdown("---")
            else:
                st.write(f"No articles for channel {channel['channel_alias']}.")
    else:
        st.error(f"Error retrieving news: {response.text}")

    return []


def get_bookmarked_article_ids(token):
    response = requests.get(
        f"{API_URL}/feed/bookmarks", headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return set(article["id"] for article in response.json())
    return set()


def add_bookmark(token, article_id):
    response = requests.post(
        f"{API_URL}/feed/bookmarks/{article_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.status_code == 201


def remove_bookmark(token, article_id):
    response = requests.delete(
        f"{API_URL}/feed/bookmarks/{article_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.status_code == 204


def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.news_loaded = False
        st.session_state.bookmarked_ids = set()

    st.title("AI-Powered News Aggregator")

    # Login sidebar
    if not st.session_state.logged_in:
        with st.sidebar:
            st.subheader("Log into your account")
            tab1, tab2 = st.tabs(["Login", "Register"])

            with tab1:
                username = st.text_input("Username", key="login_username")
                password = st.text_input(
                    "Password", type="password", key="login_password"
                )

                if st.button("Login", key="login_button"):
                    if username and password:
                        with st.spinner("Logging in..."):
                            response = login_user(username, password)
                            if response.status_code == 200:
                                st.session_state.token = response.json()["access_token"]
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.success("Login successful!")
                                st.experimental_rerun()
                            else:
                                st.error(
                                    "Login error. "
                                    f"({response.status_code}): {response.text}"
                                )
                    else:
                        st.error("Please fill in all fields.")

            with tab2:
                # --- input fields ---
                reg_username = st.text_input("Username", key="reg_username")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input(
                    "Password", type="password", key="reg_password"
                )

                # --- action button ---
                if st.button("Register", key="register_button"):
                    if reg_username and reg_email and reg_password:
                        with st.spinner("Registering..."):
                            response = register_user(
                                reg_username, reg_email, reg_password
                            )

                            # ↙ back‑end offline
                            if response is None:
                                st.error(
                                    "Cannot connect to the authentication service. "
                                    "Make sure the backend is running."
                                )
                                        # ↙ API returned a validation / business error
                                        else:
                                            try:
                                                data = response.json()
                                                msg = data.get("message", response.text)

                                                # our API returns a dict {field: message}
                                                if isinstance(msg, dict):
                                                    for m in msg.values():         # show each message separately
                                                        st.error(m)
                                                else:
                                                    st.error(f"Registration error: {msg}")

                                            except ValueError:
                                                st.error(f"Registration error: {response.text}")
                            # ↙ API returned a validation / business error
                            else:
                                try:
                                    err_msg = response.json().get(
                                        "message", response.text
                                    )
                                except ValueError:
                                    err_msg = response.text
                                st.error(f"Registration error: {err_msg}")
                    else:
                        st.error("Please fill in all fields.")

    else:
        # Authenticated user view
        st.sidebar.write(f"Welcome, {st.session_state.username}!")
        if st.sidebar.button("Logout"):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.logged_in = False
            st.session_state.news_loaded = False
            st.session_state.bookmarked_ids = set()
            st.rerun()

        # Content for authenticated users
        st.subheader("Add new channel")

        # Initialize suggested channel state if it doesn't exist
        if "suggested_channel" not in st.session_state:
            st.session_state.suggested_channel = ""

        # Get channel name from session state if a suggestion was clicked
        default_channel = st.session_state.suggested_channel

        channel_name = st.text_input(
            "Enter Telegram channel alias without @, e.g.: TechNews",
            key="channel_name",
            value=default_channel,
            placeholder="Channel name",
        )

        # Add suggested channels section
        st.markdown("### Suggested channels:")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("RBC News", key="rbc_news_btn"):
                st.session_state.suggested_channel = "rbc_news"
                st.experimental_rerun()

        with col2:
            if st.button("BBC Breaking", key="bbbreaking_btn"):
                st.session_state.suggested_channel = "bbbreaking"
                st.experimental_rerun()

        with col3:
            if st.button("Market News", key="if_market_news_btn"):
                st.session_state.suggested_channel = "if_market_news"
                st.experimental_rerun()

        # Check for prefixes and trim
        if channel_name.startswith("@"):
            channel_name = channel_name[1:]  # Remove '@'
        elif channel_name.startswith("https://t.me/"):
            channel_name = channel_name[len("https://t.me/") :]  # Remove prefix
        else:
            channel_name = channel_name

        st.markdown("""
        <style>
        .add-channel-button {
            background-color: #4361EE; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create a button using HTML
        if st.markdown('<button class="add-channel-button">Add channel</button>', unsafe_allow_html=True):
            if channel_name:
                add_channel(channel_name, st.session_state.token)
                # Clear the suggested channel after adding
                st.session_state.suggested_channel = ""
            else:
                st.error("Please enter a channel name.")

        # Sidebar filters and actions
        with st.sidebar:
            st.markdown("## Filters and Actions")
            show_only_bookmarks = st.checkbox(
                "Show only bookmarks",
                value=False,
                help="Show only articles you added to bookmarks.",
            )
            search_query = st.text_input(
                "🔍 Search articles:",
                value="",
                help=("Enter keywords to search by title or content of the article."),
            )
            if "news_data" not in st.session_state:
                st.session_state.news_data = None
            # Collect all unique categories
            news_data = st.session_state.news_data or []
            categories = set()
            for channel in news_data:
                for article in channel.get("articles", []):
                    cat = article.get("category")
                    if cat:
                        categories.add(cat)
            categories = sorted(list(categories))
            categories.insert(0, "All categories")
            selected_category = st.selectbox(
                "📂 Filter by category:",
                categories,
                help="Show only articles from the selected category.",
            )
            if st.button("Reset filters"):
                search_query = ""
                selected_category = "All categories"
                st.rerun()
            st.markdown("---")
            if st.button(
                "Update feeds", help="Get latest articles from Telegram channels."
            ):
                with st.spinner("Updating articles from channels..."):
                    update_response = requests.post(
                        f"{API_URL}/feed/update",
                        headers={"Authorization": (f"Bearer {st.session_state.token}")},
                    )
                    if update_response.status_code == 200:
                        st.success("Update started! " "Check news in a few seconds.")
                    else:
                        st.error(f"Error during update: {update_response.text}")
            if (
                st.button("Get news", help="Load and display fresh articles.")
                or st.session_state.news_data is None
            ):
                with st.spinner("Loading news..."):
                    response = requests.get(
                        (
                            f"{API_URL}/feed?"
                            "generate_summaries=true&"
                            "generate_categories=true"
                        ),
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                    )
                    if response.status_code == 200:
                        st.session_state.news_data = response.json()
                        st.session_state.news_loaded = True
                        st.success("News loaded successfully!")
                    else:
                        st.error(f"Error retrieving news: {response.text}")
                        st.session_state.news_data = []

        # Main content area
        news_data = st.session_state.news_data or []
        # Theme-aware text color
        theme = st.get_option("theme.base") if hasattr(st, "get_option") else None
        if theme == "dark":
            article_text_color = "#fff"
        else:
            article_text_color = "#222"  # dark gray for light theme
        # Get bookmarks for the user
        if "bookmarked_ids" not in st.session_state or st.session_state.get(
            "bookmarks_dirty", True
        ):
            with st.spinner("Loading bookmarks..."):
                st.session_state.bookmarked_ids = get_bookmarked_article_ids(
                    st.session_state.token
                )
                st.session_state.bookmarks_dirty = False
        bookmarked_ids = st.session_state.bookmarked_ids
        any_articles = False

        # Helper function to format date and time
        def format_datetime(date_str):
            if not date_str:
                return ""
            try:
                # Parse ISO format date
                from datetime import datetime

                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                # Format to a readable date and time
                return dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                return date_str

        for channel in news_data:
            articles = channel.get("articles", [])

            # Sort articles by published_date (newest first)
            articles = sorted(
                articles, key=lambda x: x.get("published_date", "0"), reverse=True
            )

            filtered_articles = [
                a
                for a in articles
                if (
                    selected_category == "All categories"
                    or a.get("category") == selected_category
                )
                and (
                    search_query.strip() == ""
                    or (search_query.lower() in (a.get("title") or "").lower())
                    or (search_query.lower() in (a.get("description") or "").lower())
                )
                and (not show_only_bookmarks or a.get("id") in bookmarked_ids)
            ]
            st.markdown(f"### Channel: {channel['channel_alias']} ")
            st.markdown(
                (
                    f"<span style='color: #888; font-size: 0.95em;'>"
                    f"Articles shown: <b>{len(filtered_articles)}</b>"
                    f"</span>"
                ),
                unsafe_allow_html=True,
            )
            if filtered_articles:
                any_articles = True
                for idx, article in enumerate(filtered_articles):
                    description = clean_html(article.get("description", ""))
                    title = article.get("title", "")
                    link = article.get("link", "#")
                    article_id = article.get("id")
                    is_bookmarked = article_id in bookmarked_ids
                    published_date = article.get("published_date")

                    with st.container():
                        st.markdown(
                            (
                                "<div style='background: #181c24; "
                                "border-radius: 12px; "
                                "border: 1px solid #2a2e38; padding: 1px 2px; "
                                "margin-bottom: 18px; "
                                "box-shadow: 0 2px 8px rgba(30,58,138,0.04); "
                                "display: flex; "
                                "flex-direction: column;'>"
                            ),
                            unsafe_allow_html=True,
                        )
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(
                                (
                                    f"<span style='font-size:1.15rem; "
                                    f"font-weight:600;'>"
                                    f"{title}"
                                    f"</span>"
                                ),
                                unsafe_allow_html=True,
                            )

                            # Display date and time in human readable format
                            if published_date:
                                formatted_date = format_datetime(published_date)
                                st.markdown(
                                    (
                                        f"<span style='color: #888; font-size: 0.85em;'>"
                                        f"📅 {formatted_date}"
                                        f"</span>"
                                    ),
                                    unsafe_allow_html=True,
                                )

                            if article.get("category"):
                                st.markdown(
                                    (
                                        f"<span style='color:"
                                        f"font-size:0.95em;'>"
                                        f"Category: "
                                        f"<b>{article.get('category')}</b>"
                                        f"</span>"
                                    ),
                                    unsafe_allow_html=True,
                                )
                            if article.get("ai_summary"):
                                st.info(article.get("ai_summary"), icon="🤖")
                            with st.expander("Show full article text"):
                                st.markdown(description)
                        with col2:
                            # Bookmark button
                            if article_id is not None:
                                if is_bookmarked:
                                    if st.button(
                                        "✅ Remove from bookmarks",
                                        key=f"unbookmark_{article_id}_{idx}",
                                    ):
                                        with st.spinner("Removing from bookmarks..."):
                                            if remove_bookmark(
                                                st.session_state.token, article_id
                                            ):
                                                tmp = st.session_state
                                                tmp.bookmarks_dirty = True
                                                st.success(
                                                    "Article removed " "from bookmarks!"
                                                )
                                                time.sleep(0.5)
                                                st.rerun()
                                            else:
                                                st.error(
                                                    "Error removing " "from bookmarks."
                                                )
                                else:
                                    if st.button(
                                        "🔖 Add to bookmarks",
                                        key=f"bookmark_{article_id}_{idx}",
                                    ):
                                        with st.spinner("Adding to bookmarks..."):
                                            if add_bookmark(
                                                st.session_state.token, article_id
                                            ):
                                                tst = st.session_state
                                                tst.bookmarks_dirty = True
                                                st.success(
                                                    "Article added " "to bookmarks!"
                                                )
                                                time.sleep(0.5)
                                                st.rerun()
                                            else:
                                                st.error(
                                                    "Error adding " "to bookmarks."
                                                )
                            st.markdown(
                                (
                                    f"<a href='{link}' target='_blank' "
                                    f"style='display:inline-block; "
                                    f"padding:8px 18px; "
                                    f"background:#4361EE; color:white; "
                                    f"border-radius:6px; "
                                    f"text-decoration:none; font-size:0.98em; "
                                    f"margin-top:8px;'>"
                                    "Read on Telegram</a>"
                                ),
                                unsafe_allow_html=True,
                            )
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning(
                    (
                        f"No articles for selected category "
                        f"and/or search query in channel "
                        f"{channel['channel_alias']}."
                    )
                )
        if not any_articles:
            st.info(
                (
                    "No articles matching the selected filters "
                    "or search query. "
                    "Try changing filters or updating articles."
                ),
                icon="ℹ️",
            )

    # Fix remaining UI elements for channel update
    if st.session_state.logged_in:
        with st.sidebar:
            # Add refresh button
            st.subheader("Update Feeds")
            if st.button("Update All Channels", key="update_all"):
                with st.spinner("Updating articles from channels..."):
                    update_response = requests.post(
                        f"{API_URL}/feed/update",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                    )
                    if update_response.status_code == 200:
                        st.success("Channels updated!")
                        st.session_state.news_loaded = False
                        st.experimental_rerun()
                    else:
                        st.error(f"Error during update: {update_response.text}")


if __name__ == "__main__":
    main()
