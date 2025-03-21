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
    password = st.text_input("🔑 Password", type="password", key="register_password")
    confirm_password = st.text_input("🔑 Confirm Password", type="password", key="confirm_password")

    # Role selection
    role = st.radio("Select Role", ["Student", "Teacher"], key="register_role")

    # Additional fields based on role
    if role == "Student":
        up_id = st.text_input("🎓 University ID", key="register_up_id")
        course = st.text_input("📚 Course", key="register_course")
        year = st.number_input("📅 Year", min_value=1, max_value=5, step=1, key="register_year")

    elif role == "Teacher":
        available_courses = ["Math", "Science", "History", "Computer Science", "English"]  # Example courses
        courses = st.multiselect("📖 Select Courses", available_courses, key="register_courses")

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
        else:
            # Prepare user data
            hashed_password = hash_password(password)
            user_data = {
                "email": email,
                "password": hashed_password,
                "role": role,
                "up_id": up_id if role == "Student" else None,
                "course": course if role == "Student" else None,
                "year": year if role == "Student" else None,
                "courses": courses if role == "Teacher" else None,
            }

            if register_user(user_data):
                #st.session_state["logged_in"] = True
                #st.session_state["user_email"] = email
                cookies["logged_in"] = "True"
                cookies["user_email"] = email
                cookies.save()
                #st.success("✅ Registration successful! You can now log in.")
                st.rerun()

def register_user(user_data):
    conn = get_db_connection()
    cur = conn.cursor()

    teacher_courses = ",".join(user_data["courses"]) if user_data["courses"] else None

    # Insert user into database
    cur.execute(
        'INSERT INTO "users" (email, password, role, up_id, course, year, courses) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
        (user_data["email"], user_data["password"], user_data["role"], user_data["up_id"], user_data["course"], user_data["year"], teacher_courses)
    )

    conn.commit()
    cur.close()
    conn.close()
    
    return True

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

def send_message(user_input, user_email):
    url = "http://rasa:5005/webhooks/rest/webhook"
    payload = {
        "sender": user_email,
        "message": user_input,
        "metadata": {"user_email": user_email}
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        messages = response.json()

        if messages:
            bot_replies = [msg["text"] for msg in messages if "text" in msg]
            bot_reply = "\n\n".join(bot_replies)
            return bot_reply

        return "🤖 Sorry, I didn't understand that."
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
def get_class_progress(class_name):
    if not class_name:
        return pd.DataFrame()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all students up_ids in the class (separated by commas)
    cur.execute("SELECT students FROM classes WHERE name = %s", (class_name,))
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