import streamlit as st
import requests 
import re
import os

# Get API URL from environment or use default
API_URL = os.environ.get("API_URL", "http://web:8000")

def add_channel(channel_name):
    if not channel_name:
        st.error("Пожалуйста, введите имя канала.")
    if channel_name and not re.match(r"^[A-Za-z0-9_]+$", channel_name):
        st.error("Имя канала должно содержать только латиницу, цифры и '_'")
    else:
        response = requests.post(
            f"{API_URL}/feed",  
            json={"UserID": "example_user_id", "Channel_alias": f"@{channel_name}"}  
        )
        if response.status_code == 200:
            st.success(f"Канал @{channel_name} добавлен!")
        else:
            st.error("Ошибка при добавлении канала.")

def get_news(user_id):
    if user_id:
        response = requests.get(f"{API_URL}/feed?userID={user_id}")
        if response.status_code == 200:
            return response.json()  
        else:
            st.error("Ошибка при получении новостей.")
    return []
    # return [
    #     {
    #         "title": "Первая новость",
    #         "description": "Описание первой новости. Описание первой новости. Описание первой новости. Описание первой новости.",
    #         "link": "http://example.com/first-news"
    #     },
    #     {
    #         "title": "Вторая новость",
    #         "description": "Описание второй новости.",
    #         "link": "http://example.com/second-news"
    #     },
    #     {
    #         "title": "Третья новость",
    #         "description": "Описание третьей новости. Описание первой новости. Описание первой новости. Описание первой новости. Описание первой новости. Описание первой новости. ",
    #         "link": "http://example.com/third-news"
    #     }
    # ]

def main():
    st.title("Получить новости")

    # Fixed '@' prefix for the channel name
    channel_name_input = st.text_input("Введите имя Telegram канала:", value="", placeholder="Имя канала")

    # Check for prefixes and trim
    if channel_name_input.startswith("@"):
        channel_name = channel_name_input[1:]  # Remove '@'
    elif channel_name_input.startswith("https://t.me/"):
        channel_name = channel_name_input[len("https://t.me/"):]  # Remove prefix
    else:
        channel_name = channel_name_input
    
    if st.button("Добавить"):
        if channel_name:
            add_channel(channel_name)
        else:
            st.error("Пожалуйста, введите имя канала.")

    # Add space after the button
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Input field for user ID
    user_id = st.text_input("Введите ваш user ID:", value="", placeholder="user ID")


    # Button to get news
    if st.button("Получить новости"):
        news = get_news(user_id)
        if news:
                for article in news:
                    # Using HTML to create a rectangle
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
            st.write("Нет новостей для отображения.")

if __name__ == "__main__":
    main() 