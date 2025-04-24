import streamlit as st
import requests 
import re

def add_channel(channel_name):
    if not channel_name:
        st.error("Пожалуйста, введите имя канала.")
    if channel_name and not re.match(r"^[A-Za-z0-9_]+$", channel_name):
        st.error("Имя канала должно содержать только латиницу, цифры и '_'")
    else:
        response = requests.post(
            "http://localhost:8000/feed",  # URL вашего API
            json={"UserID": "example_user_id", "Channel_alias": f"@{channel_name}"}  # Данные для отправки
        )
        if response.status_code == 200:
            st.success(f"Канал @{channel_name} добавлен!")
        else:
            st.error("Ошибка при добавлении канала.")

def main():
    st.title("Добавить Telegram Канал")

    # Fixed '@' prefix for the channel name
    channel_name_input = st.text_input("Введите имя Telegram канала:", value="", placeholder="Имя канала")

    # Проверка на наличие префиксов и обрезка
    if channel_name_input.startswith("@"):
        channel_name = channel_name_input[1:]  # Убираем '@'
    elif channel_name_input.startswith("https://t.me/"):
        channel_name = channel_name_input[len("https://t.me/"):]  # Убираем префикс
    else:
        channel_name = channel_name_input  # Оставляем как есть

    
    if st.button("Добавить"):
        if channel_name:
            add_channel(channel_name)
        else:
            st.error("Пожалуйста, введите имя канала.")


if __name__ == "__main__":
    main()