import streamlit as st
import re
import hashlib
import psycopg2
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
from time import sleep
from streamlit_extras.stylable_container import stylable_container
from psycopg2.extras import RealDictCursor
import pandas as pd
import requests
import json

from shared_models.models import db, Users, Student, Teacher, Classes

# Generate a strong secret key for your application
SECRET_KEY = "your_strong_secret_key_here"

# Cookie manager with password
cookies = EncryptedCookieManager(prefix="chatbot_app_", password=SECRET_KEY)

if not cookies.ready():
    st.stop()

# Database connection
DB_CONFIG = {
    "dbname": "chatbotdb",
    "user": "admin",
    "password": "password",
    "host": "db",  # Docker service name
    "port": 5432
}


def fetch_course_classes(course):
    response = requests.get("http://flask-server:8080/api/course_classes/" + course)
    return response.json() if response.status_code == 200 else {}

def fetch_classes():
    response = requests.get("http://flask-server:8080/api/classes")
    return response.json() if response.status_code == 200 else {}

def fetch_teacher_classes(teacher_email):
    response = requests.get("http://flask-server:8080/api/teacher_classes/" + teacher_email)
    return response.json() if response.status_code == 200 else {}

def fetch_class_progress(class_id):
    response = requests.get("http://flask-server:8080/api/class_progress/" + str(class_id))
    return response.json() if response.status_code == 200 else {}

def fetch_student_progress(student_email):
    student_up = fetch_student(student_email).get("student_up")
    response = requests.get("http://flask-server:8080/api/student_progress/" + str(student_up))
    return response.json() if response.status_code == 200 else {}

def fetch_student(student_email):
    response = requests.get("http://flask-server:8080/api/get_student/" + student_email)
    return response.json() if response.status_code == 200 else {}

def fetch_user(user_email):
    response = requests.get("http://flask-server:8080/api/get_user/" + user_email)
    return response.json() if response.status_code == 200 else {}

def fetch_message_history(user_email):
    user = fetch_user(user_email)
    if user:
        user_id = user.get("id")
        response = requests.get("http://flask-server:8080/api/message_history/" + str(user_id))
        return response.json() if response.status_code == 200 else {}
    return {}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_user_role(user_email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT role FROM "users" WHERE email = %s', (user_email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user['role']

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
        if authenticate_user(email, password):
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
        st.info("df_classes: " + str(df_classes))

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
        #elif not is_strong_password(password):
            #st.error("❌ Password must be at least 8 characters long, contain uppercase and lowercase letters, digits, and special characters.")
            #return
        if password != confirm_password:
            st.error("❌ Passwords do not match!")
            return
        elif user_exists(email):
            st.error("❌ Email already registered! Try logging in.")
            return
        
        # Create new user
        hashed_password = hash_password(password)
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Insert user into database
            cur.execute(
                'INSERT INTO "users" (name, role, email, password) VALUES (%s, %s, %s, %s) RETURNING id',
                (name, role, email, hashed_password)
            )

            # get the user id
            user_id = cur.fetchone()[0]

            if role == "Student":
                selected_class_codes = ",".join(selected_class_codes)                
                cur.execute(
                    'INSERT INTO "student" (up, user_id, course, year, classes) VALUES (%s, %s, %s, %s, %s)',
                    (up, user_id, course, year, selected_class_codes)
                )
            elif role == "Teacher":
                selected_class_codes = ",".join(selected_class_codes)
                cur.execute(
                    'INSERT INTO "teacher" (user_id, classes) VALUES (%s, %s) RETURNING id',
                    (user_id, selected_class_codes)
                )
            
            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            st.error(f"❌ Registration failed: {e}")
            sleep(2)
            st.rerun()
        
        cookies["logged_in"] = "True"
        cookies["user_email"] = email
        cookies.save()
        st.rerun()


# Hash passwords before storing them
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def authenticate_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    hashed_password = hash_password(password)
    cur.execute('SELECT * FROM "users" WHERE email = %s AND password = %s', (email, hashed_password))
    user = cur.fetchone()
    if user:
        cur.close()
        conn.close()
        return True
    return False

# Check if user already exists
def user_exists(email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM "users" WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

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
    
def save_chat_history(user_email, user_message, bot_response):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT id FROM "users" WHERE email = %s', (user_email,))
    user = cur.fetchone()

    if user:
        user_id = user['id']
        cur.execute(
            "INSERT INTO message_history (user_id, question, response, timestamp) VALUES (%s, %s, %s, NOW())",
            (user_id, user_message, bot_response)
        )
        conn.commit()
    
    cur.close()
    conn.close()

# Function to fetch student progress for a teacher’s classes
def get_class_progress(class_code, class_number):

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT id FROM "classes" WHERE code = %s and number = %s', (class_code, class_number))
    data = cur.fetchone()

    class_id = None
    if data:
        class_id = data['id']
    st.info("class_id: " + str(class_id))

    cur.close()
    conn.close()

    progress = fetch_class_progress(class_id)
    if progress:
        return progress
    else:
        st.info(f"No progress data found for class: {class_code}-{class_number}")
        return pd.DataFrame()

