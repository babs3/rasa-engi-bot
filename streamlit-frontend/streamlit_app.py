import streamlit as st
import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import streamlit.components.v1 as components
from streamlit_scroll_to_top import scroll_to_here
from datetime import datetime
import re

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

# Streamlit UI
def main():
    st.set_page_config(page_title="Chatbot", layout="wide")

    # Sidebar for logout
    with st.sidebar:
        st.title("Chatbot")
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            st.write(f"Logged in as **{st.session_state['user_email']}**")
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()
        else:
            st.info("Please log in or register.")

    # Authentication
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = ""

    if not st.session_state["logged_in"]:
        auth_tabs()
    else:
        chat_interface()

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$'
    return re.match(pattern, password) is not None

def auth_tabs():
    st.title("🔑 Authentication")
    tab1, tab2 = st.tabs(["Login", "Register"])

    st.session_state["scroll_down"] = True
    st.session_state["separator_displayed"] = False

    with tab1:
        login_form()

    with tab2:
        register_form()

def login_form():
    st.subheader("Login to Your Account")
    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔒 Password", type="password", key="login_password")

    if st.button("Login"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format!")
            return
        if authenticate_user(email, password):
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = email
            st.session_state["messages"] = load_chat_history(email)  # Load previous messages
            st.success("✅ Login successful! Your previous chat history has been loaded.")
            st.rerun()
        else:
            st.error("❌ Invalid email or password!")

def load_chat_history(user_email):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute('SELECT user_message, bot_response FROM user_history WHERE user_id = (SELECT id FROM "user" WHERE email = %s) ORDER BY timestamp ASC', (user_email,))
    history = cur.fetchall()

    cur.close()
    conn.close()

    messages = []
    for entry in history:
        messages.append({"role": "user", "content": entry["user_message"]})
        messages.append({"role": "assistant", "content": entry["bot_response"]})

    return messages  # Return structured messages

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
        elif not is_strong_password(password):
            st.error("❌ Password must be at least 8 characters long, contain uppercase and lowercase letters, digits, and special characters.")
            return
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
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                st.success("✅ Registration successful! You can now log in.")
                st.rerun()

def register_user(user_data):
    conn = get_db_connection()
    cur = conn.cursor()

    teacher_courses = ",".join(user_data["courses"]) if user_data["courses"] else None

    # Insert user into database
    cur.execute(
        'INSERT INTO "user" (email, password, role, up_id, course, year, courses) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
        (user_data["email"], user_data["password"], user_data["role"], user_data["up_id"], user_data["course"], user_data["year"], teacher_courses)
    )
    #user_id = cur.fetchone()[0]

    # Insert teacher courses if applicable
    #if user_data["role"] == "Teacher" and user_data["courses"]:
    #    for course in user_data["courses"]:
    #        cur.execute('INSERT INTO teacher_courses (user_id, course) VALUES (%s, %s)', (user_id, course))

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
    cur.execute('SELECT * FROM "user" WHERE email = %s AND password = %s', (email, hashed_password))
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
    cur.execute('SELECT * FROM "user" WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None


def chat_interface():
    st.title("💬 Chat with Rasa Bot")
    st.write(f"**User:** {st.session_state['user_email']}")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display separator after the last past message
    if not st.session_state.separator_displayed:
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced separator styling
        st.markdown(
            f"""
            <div style='border-top: 2px solid #4CAF50; margin-top: 20px; margin-bottom: 10px;'></div>
            <div style='text-align: center; font-size: 14px; color: #4CAF50; margin-bottom: 20px;'>
                📅 New Messages - {current_date}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.session_state.separator_displayed = True

    # Handle scrolling to the bottom
    if st.session_state.scroll_down:
        scroll_to_here(0, key='bottom')  # Smooth scroll to the bottom of the page
        st.session_state.scroll_down = False  # Reset the scroll state

    user_input = st.text_input("Type your message...", key="user_input")
    send_button = st.button("Send", use_container_width=True)

    if send_button and user_input:
        response = send_message(user_input, st.session_state["user_email"])
        if response:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.session_state["messages"].append({"role": "assistant", "content": response})
            save_chat_history(st.session_state["user_email"], user_input, response)
        
        st.rerun()

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

    cur.execute('SELECT id FROM "user" WHERE email = %s', (user_email,))
    user = cur.fetchone()

    if user:
        user_id = user['id']
        cur.execute(
            "INSERT INTO user_history (user_id, user_message, bot_response, timestamp) VALUES (%s, %s, %s, NOW())",
            (user_id, user_message, bot_response)
        )
        conn.commit()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
