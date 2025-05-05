import streamlit as st
import requests 
import re
import os
from bs4 import BeautifulSoup
import html

# Get API URL from environment or use default
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Authentication functions
def register_user(username, email, password):
    """Register a new user."""
    response = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "email": email, "password": password}
    )
    return response

def login_user(username, password):
    """Login and get access token."""
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return response

def add_channel(channel_name, token):
    if not channel_name:
        st.error("Пожалуйста, введите имя канала.")
        return
    
    if not re.match(r"^[A-Za-z0-9_]+$", channel_name):
        st.error("Имя канала должно содержать только латиницу, цифры и '_'")
        return
    
    response = requests.post(
        f"{API_URL}/feed",  
        json={"Channel_alias": f"@{channel_name}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        st.success(f"Канал @{channel_name} добавлен!")
    else:
        st.error(f"Ошибка при добавлении канала: {response.text}")

def clean_html(html_content):
    """Clean HTML content and extract plain text."""
    # Replace HTML tags with appropriate markdown or remove them
    if not html_content:
        return ""
    
    # Use BeautifulSoup to parse HTML if possible
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text()
    except:
        # Fallback to regex replacements if BeautifulSoup fails
        text = re.sub(r'<[^>]*>', '', html_content)
        return text

def get_news(token, generate_summaries=False, generate_categories=False):
    if not token:
        st.error("Вы не авторизованы. Пожалуйста, войдите в систему.")
        return []
    
    # Custom CSS for better styling
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    response = requests.get(
        f"{API_URL}/feed?generate_summaries={str(generate_summaries).lower()}&generate_categories={str(generate_categories).lower()}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Проходим по каждому каналу
        for channel in data:
            st.subheader(f"Канал: {channel['channel_alias']}")
            articles = channel.get('articles', [])
            if articles:  # Проверяем, есть ли статьи
                for idx, article in enumerate(articles):
                    # Clean description/content from HTML tags
                    description = clean_html(article.get('description', ''))
                    title = article.get('title', '')
                    link = article.get('link', '#')
                    
                    # Create article card with proper layout
                    with st.container():
                        # Use columns for better layout
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            # Display title
                            st.markdown(f"### {title}")
                            
                            # Display category if available
                            if article.get('category'):
                                st.markdown(f"**Category:** {article.get('category')}")
                            
                            # Display AI summary first if available
                            if article.get('ai_summary'):
                                st.markdown("**AI Summary:**")
                                st.info(article.get('ai_summary'))
                            
                            # Hide full article text in an accordion
                            with st.expander("Show Full Article"):
                                st.markdown(description)
                        
                        with col2:
                            # Add direct link instead of a button
                            st.markdown(f"[Читать в Telegram]({link})", unsafe_allow_html=False)
                        
                        # Add separator between articles
                        st.markdown("---")
            else:
                st.write(f"Нет статей для канала {channel['channel_alias']}.")
    else:
        st.error(f"Ошибка при получении новостей: {response.text}")
    
    return []

def main():
    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    
    st.title("AI-Powered News Aggregator")
    
    # Authentication section
    if not st.session_state.is_authenticated:
        tab1, tab2 = st.tabs(["Вход", "Регистрация"])
        
        with tab1:
            st.subheader("Войдите в свой аккаунт")
            username = st.text_input("Имя пользователя", key="login_username")
            password = st.text_input("Пароль", type="password", key="login_password")
            
            if st.button("Войти"):
                if username and password:
                    response = login_user(username, password)
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = username
                        st.session_state.is_authenticated = True
                        st.success("Вход выполнен успешно!")
                        st.experimental_rerun()
                    else:
                        st.error("Ошибка входа. Проверьте ваши учетные данные.")
                else:
                    st.error("Пожалуйста, заполните все поля.")
        
        with tab2:
            st.subheader("Создайте новый аккаунт")
            new_username = st.text_input("Имя пользователя", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Пароль", type="password", key="reg_password")
            confirm_password = st.text_input("Подтвердите пароль", type="password", key="confirm_password")
            
            if st.button("Зарегистрироваться"):
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Пароли не совпадают!")
                    else:
                        response = register_user(new_username, new_email, new_password)
                        if response.status_code == 200:
                            st.success("Регистрация успешна! Теперь вы можете войти.")
                            # Automatically login
                            login_response = login_user(new_username, new_password)
                            if login_response.status_code == 200:
                                data = login_response.json()
                                st.session_state.token = data["access_token"]
                                st.session_state.username = new_username
                                st.session_state.is_authenticated = True
                                st.experimental_rerun()
                        else:
                            st.error(f"Ошибка регистрации: {response.text}")
                else:
                    st.error("Пожалуйста, заполните все поля.")
    
    else:
        # Authenticated user view
        st.sidebar.write(f"Привет, {st.session_state.username}!")
        if st.sidebar.button("Выйти"):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.is_authenticated = False
            st.experimental_rerun()
        
        # Content for authenticated users
        st.subheader("Добавить новый канал")
        channel_name_input = st.text_input("Введите имя Telegram канала:", value="", placeholder="Имя канала")

        # Check for prefixes and trim
        if channel_name_input.startswith("@"):
            channel_name = channel_name_input[1:]  # Remove '@'
        elif channel_name_input.startswith("https://t.me/"):
            channel_name = channel_name_input[len("https://t.me/"):]  # Remove prefix
        else:
            channel_name = channel_name_input
        
        if st.button("Добавить канал"):
            if channel_name:
                add_channel(channel_name, st.session_state.token)
            else:
                st.error("Пожалуйста, введите имя канала.")

        # Sidebar filters and actions
        with st.sidebar:
            st.markdown("## Фильтры и действия")
            search_query = st.text_input("🔍 Поиск по статьям:", value="", help="Введите ключевые слова для поиска по заголовку или содержимому статьи.")
            if 'news_data' not in st.session_state:
                st.session_state.news_data = None
            # Collect all unique categories
            news_data = st.session_state.news_data or []
            categories = set()
            for channel in news_data:
                for article in channel.get('articles', []):
                    cat = article.get('category')
                    if cat:
                        categories.add(cat)
            categories = sorted(categories)
            categories.insert(0, 'Все категории')
            selected_category = st.selectbox("📂 Фильтр по категории:", categories, help="Показать только статьи выбранной категории.")
            if st.button("Сбросить фильтры"):
                search_query = ""
                selected_category = 'Все категории'
                st.experimental_rerun()
            st.markdown("---")
            if st.button("Обновить статьи", help="Получить последние статьи из каналов Telegram."):
                with st.spinner("Обновление статей из каналов..."):
                    update_response = requests.post(
                        f"{API_URL}/feed/update",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if update_response.status_code == 200:
                        st.success("Обновление запущено! Проверьте новости через несколько секунд.")
                    else:
                        st.error(f"Ошибка при обновлении: {update_response.text}")
            if st.button("Получить новости", help="Загрузить и отобразить свежие статьи.") or st.session_state.news_data is None:
                with st.spinner("Загрузка новостей..."):
                    response = requests.get(
                        f"{API_URL}/feed?generate_summaries=true&generate_categories=true",
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    if response.status_code == 200:
                        st.session_state.news_data = response.json()
                        st.success("Новости успешно загружены!")
                    else:
                        st.error(f"Ошибка при получении новостей: {response.text}")
                        st.session_state.news_data = []

        # Main content area
        news_data = st.session_state.news_data or []
        any_articles = False
        for channel in news_data:
            articles = channel.get('articles', [])
            filtered_articles = [
                a for a in articles
                if (selected_category == 'Все категории' or a.get('category') == selected_category)
                and (
                    search_query.strip() == ""
                    or (search_query.lower() in (a.get('title') or '').lower())
                    or (search_query.lower() in (a.get('description') or '').lower())
                )
            ]
            st.markdown(f"### Канал: {channel['channel_alias']} ")
            st.markdown(f"<span style='color: #888; font-size: 0.95em;'>Показано статей: <b>{len(filtered_articles)}</b></span>", unsafe_allow_html=True)
            if filtered_articles:
                any_articles = True
                for idx, article in enumerate(filtered_articles):
                    description = clean_html(article.get('description', ''))
                    title = article.get('title', '')
                    link = article.get('link', '#')
                    with st.container():
                        st.markdown(
                            """
                            <div style='background: #181c24; border-radius: 12px; border: 1px solid #2a2e38; padding: 1px 2px; margin-bottom: 18px; box-shadow: 0 2px 8px rgba(30,58,138,0.04);'>
                            """,
                            unsafe_allow_html=True
                        )
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"<span style='font-size:1.15rem; font-weight:600; color:#fff'>{title}</span>", unsafe_allow_html=True)
                            if article.get('category'):
                                st.markdown(f"<span style='color:#fff; font-size:0.95em;'>Категория: <b>{article.get('category')}</b></span>", unsafe_allow_html=True)
                            if article.get('ai_summary'):
                                st.info(article.get('ai_summary'), icon="🤖")
                            with st.expander("Показать полный текст статьи"):
                                st.markdown(description)
                        with col2:
                            st.markdown(f"<a href='{link}' target='_blank' style='display:inline-block; padding:8px 18px; background:#4361EE; color:white; border-radius:6px; text-decoration:none; font-size:0.98em; margin-top:8px;'>Читать в Telegram</a>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning(f"Нет статей для выбранной категории и/или поискового запроса в канале {channel['channel_alias']}.")
        if not any_articles:
            st.info("Нет статей, соответствующих выбранным фильтрам или поисковому запросу. Попробуйте изменить фильтры или обновить статьи.", icon="ℹ️")

if __name__ == "__main__":
    main() 