import streamlit as st
import re
import hashlib
from datetime import datetime
from time import sleep
import pandas as pd
import requests
import json
import os

from shared.flask_requests import *

CURRENT_CLASS = os.getenv("CURRENT_CLASS")

def is_authorized(student_email):
    student = fetch_student(student_email)
    student_classes = student.get("classes")
    student_classes = student_classes.split(",") if len(student_classes) > 1 else student_classes

    authorized = False
    for class_ in student_classes:
        code, _ = class_.split("-")
        if code == CURRENT_CLASS:
            authorized = True
            break
    if not authorized:
        st.info(f"❌ Student not in the current class: {CURRENT_CLASS}")
        return False
    return True
    
def get_user_role(user_email):
    user = fetch_user(user_email)
    if user:
        return user.get("role")
    return None

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$'
    return re.match(pattern, password) is not None

def load_chat_history(user_email):
    history = fetch_message_history(user_email)
    if not history:
        st.info("No chat history found for this user.")
        return []

    messages = []
    for entry in history:
        messages.append({"role": "user", "content": entry.get("question")})
        messages.append({"role": "assistant", "content": entry.get("response")})

    return messages  # Return structured messages

def is_valid_up(up):
    # up must be a number of 9 digits
    return up.isdigit() and len(up) == 9

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def display_message_separator():
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f"""
        <div style='border-top: 2px solid #4CAF50; margin-top: 20px; margin-bottom: 10px;'></div>
        <div style='text-align: center; font-size: 14px; color: #4CAF50; margin-bottom: 20px;'>
            📅 New Messages - {current_date}
        </div>
        """,
        unsafe_allow_html=True
    )

def send_message(user_input, user_email, selected_class_name=None, selected_class_number=None, teacher_question=None):
    url = "http://rasa:5005/webhooks/rest/webhook"
    payload = {
        "sender": user_email,
        "message": user_input,
        "metadata": {"selected_class_name": selected_class_name, "selected_class_number": selected_class_number, "teacher_question": teacher_question}
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        messages = response.json()

        bot_reply = ""
        buttons = []

        for message in messages:
            if "text" in message:
                bot_reply += f"\n\n {message['text']}"
            if "buttons" in message:
                buttons = message["buttons"]

        return bot_reply.strip(), buttons  # Return both text and buttons

    except requests.RequestException as e:
        st.error(f"⚠️ Error connecting to Rasa: {e}")
        return None
    
