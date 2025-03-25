import streamlit as st
import re
import hashlib
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
from time import sleep
import pandas as pd
import requests
import json
import os

from shared.flask_requests import *

# Generate a strong secret key for your application
SECRET_KEY = "your_strong_secret_key_here" # ??
CURRENT_CLASS = os.getenv("CURRENT_CLASS")

# Cookie manager with password
cookies = EncryptedCookieManager(prefix="chatbot_app_", password=SECRET_KEY)
if not cookies.ready():
    st.stop()


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

def login_form():
    st.subheader("Login to Your Account")
    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔒 Password", type="password", key="login_password")

    if st.button("Login"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format!")
            return
        response = authenticate_user(email, password).get("status_code")
        if response != {}:
            cookies["logged_in"] = "True"
            cookies["user_email"] = email
            cookies.save()
            #st.success("✅ Login successful! Your previous chat history has been loaded.")
            st.rerun()
        else:
            st.error("❌ Invalid email or password!")

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

def register_form():
    st.subheader("Create a New Account")

    # Basic user details
    email = st.text_input("📧 Email", key="register_email")
    name = st.text_input("👤 Name", key="register_name")
    password = st.text_input("🔑 Password", type="password", key="register_password")
    confirm_password = st.text_input("🔑 Confirm Password", type="password", key="confirm_password")

    # Role selection
    role = st.radio("Select Role", ["Student", "Teacher"], key="register_role")

    # Additional fields based on role
    if role == "Student":
        up = st.text_input("🎓 University ID", key="register_up_id")
        year = st.number_input("📅 Year", min_value=1, max_value=5, step=1, key="register_year")
        course = st.text_input("📚 Course", key="register_course")

        # Get classes from Flask API
        available_classes = fetch_classes()
        df_classes = pd.DataFrame(available_classes)

        # Create class code-number pairs
        df_classes["class_code_number"] = df_classes["code"] + "-" + df_classes["number"]
        class_codes = df_classes["class_code_number"].unique()
        selected_class_codes = st.multiselect("📖 Select Classes", class_codes, key="register_classes")

    elif role == "Teacher":
        available_classes = fetch_classes()  # Get classes from Flask API
        class_codes = [c["code"] for c in available_classes]
        class_codes = list(set(class_codes))  # Remove duplicates
        selected_class_codes = st.multiselect("📖 Select Classes", class_codes, key="register_classes")

    if st.button("Register"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format!")
            return
        #if not is_strong_password(password):
            #st.error("❌ Password must be at least 8 characters long, contain uppercase and lowercase letters, digits, and special characters.")
            #return
        #if not is_valid_up(up):
            #st.error("❌ Invalid University ID!")
        if password != confirm_password:
            st.error("❌ Passwords do not match!")
            return
        if fetch_user(email):            
            st.error("❌ Email already registered! Try logging in.")
            return
        
        # Create new user
        hashed_password = hash_password(password)
        selected_class_codes = ",".join(selected_class_codes)

        if role == "Student":
            register_student(name, email, hashed_password, up, course, year, selected_class_codes)
        elif role == "Teacher":
            register_teacher(name, email, hashed_password, selected_class_codes)
        
        cookies["logged_in"] = "True"
        cookies["user_email"] = email
        cookies.save()
        st.rerun()


# Hash passwords before storing them
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def logout():
    st.session_state.clear()
    cookies["logged_in"] = "False"
    cookies["user_email"] = ""
    cookies["display_message_separator"] = "True"
    cookies.save()
    sleep(1)  
    st.rerun()

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
    
