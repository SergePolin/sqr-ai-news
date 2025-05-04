import streamlit as st
import requests 
import re
import os

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

def get_news(token):
    if not token:
        st.error("Вы не авторизованы. Пожалуйста, войдите в систему.")
        return []
    
    response = requests.get(
        f"{API_URL}/feed",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Проходим по каждому каналу
        for channel in data:
            st.subheader(f"Канал: {channel['channel_alias']}")
            articles = channel.get('articles', [])
            if articles:  # Проверяем, есть ли статьи
                for article in articles:
                    # Выводим информацию о статье
                    st.markdown(
                        f"""
                        <div style='background-color: rgba(240, 240, 240, 0.2); padding: 10px; margin: 10px 0; border-radius: 5px;'>
                            <h4>{article['title']}</h4>
                            <p>{article['description']}</p>
                            <a href="{article['link']}">Читать далее</a>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
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

        # Button to get news
        if st.button("Получить новости"):
            get_news(st.session_state.token)

if __name__ == "__main__":
    main() 