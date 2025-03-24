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


def fetch_classes():
    response = requests.get("http://flask-server:8080/api/classes")
    return response.json() if response.status_code == 200 else {}

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
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT question, response FROM message_history WHERE user_id = (SELECT id FROM "users" WHERE email = %s) ORDER BY timestamp ASC', (user_email,))
    history = cur.fetchall()

    cur.close()
    conn.close()

    messages = []
    for entry in history:
        messages.append({"role": "user", "content": entry["question"]})
        messages.append({"role": "assistant", "content": entry["response"]})

    return messages  # Return structured messages

def get_student_progress(user_email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT question, response, topic, pdfs, timestamp
        FROM student_progress
        WHERE student_up_id = (SELECT up_id FROM "users" WHERE email = %s)
        ORDER BY timestamp ASC;
    """, (user_email,))
    data = cur.fetchall()
    cur.close()
    conn.close()

    return pd.DataFrame(data, columns=["question", "response", "topic", "pdfs", "timestamp"])

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
        course = st.text_input("📚 Course", key="register_course")
        year = st.number_input("📅 Year", min_value=1, max_value=5, step=1, key="register_year")

    elif role == "Teacher":

        available_classes = fetch_classes()  # Get classes from Flask API
        st.info(available_classes)
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

            #cur.execute('SELECT id FROM "users" WHERE email = %s', (user_email,))
            #user = cur.fetchone()
            #user_id = user['id']

            # get the user id
            user_id = cur.fetchone()[0]
            st.info(user_id)

            if role == "Student":
                cur.execute(
                    'INSERT INTO "student" (up, user_id, course, year) VALUES (%s, %s, %s, %s) RETURNING id',
                    (up, user_id, course, year)
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
            db.session.rollback()
            st.error(f"❌ Registration failed: {e}")
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

# Function to fetch teacher's classes
def get_teacher_classes(teacher_email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, course, name, number, students FROM classes WHERE teachers LIKE %s;
    """, (f"%{teacher_email}%",))
    classes = cur.fetchall()
    conn.close()

    return pd.DataFrame(classes, columns=["id", "course", "name", "number", "students"])

# Function to fetch student progress for a teacher’s classes
def get_class_progress(class_name, class_number):
    if not class_name or not class_number:
        return pd.DataFrame()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all students up_ids in the class (separated by commas)
    cur.execute("SELECT students FROM classes WHERE name = %s and number = %s", (class_name,class_number))
    data = cur.fetchone()
    
    if not data or not data['students']:
        cur.close()
        conn.close()
        return pd.DataFrame()

    students = data['students'].split(",")

    # Get all student progress for each student in the class
    data = []
    for student in students:
        cur.execute("""
            SELECT student_up_id, question, response, topic, pdfs, timestamp
            FROM student_progress
            WHERE student_up_id = %s
            ORDER BY timestamp ASC;
        """, (student,))
        student_data = cur.fetchall()
        if student_data:
            data += student_data

    cur.close()
    conn.close()

    if not data:
        st.info(f"No progress data found for students in class: {class_name}")
        return pd.DataFrame()

    return pd.DataFrame(data, columns=["student_up_id", "question", "response", "topic", "pdfs", "timestamp"])