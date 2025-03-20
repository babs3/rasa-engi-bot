import streamlit as st

st.set_page_config("Engi-bot", '🤖', layout="wide")

import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from streamlit_scroll_to_top import scroll_to_here
from datetime import datetime
import re
from streamlit_cookies_manager import EncryptedCookieManager
from time import sleep
import warnings
import pandas as pd

# Suppress Streamlit deprecation warnings
warnings.filterwarnings("ignore")

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

# Streamlit UI
def main():

    # Sidebar for logout
    with st.sidebar:
        st.title("Engi-bot")
        #if "logged_in" in st.session_state and st.session_state["logged_in"]:
        if cookies.get("logged_in") == "True":
            user_email = cookies.get("user_email")
            st.write(f"Logged in as **{user_email}**")
            if st.button("Logout"):
                st.session_state.clear()
                cookies["logged_in"] = "False"
                cookies["user_email"] = ""
                cookies["display_message_separator"] = "True"
                cookies.save()
                sleep(1)  # Add a delay to give time to save cookies
                st.rerun()
            
            set_student_insights(user_email)

        else:
            st.info("Please log in or register.")

    #if "scroll_down" not in st.session_state:
    st.session_state["scroll_down"] = True
    
    if "display_message_separator" not in cookies:
        cookies["display_message_separator"] = "True"
    
    if "input_disabled" not in st.session_state:
        st.session_state.input_disabled = "False"

        
    if cookies.get("logged_in") != "True":
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
            cookies["logged_in"] = "True"
            cookies["user_email"] = email
            cookies.save()
            st.success("✅ Login successful! Your previous chat history has been loaded.")
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
        WHERE student_id = (SELECT id FROM "users" WHERE email = %s)
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
        elif not is_strong_password(password):
            st.error("❌ Password must be at least 8 characters long, contain uppercase and lowercase letters, digits, and special characters.")
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
                st.success("✅ Registration successful! You can now log in.")
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

def chat_interface():
    st.title("💬 Chat with EngiBot")

    if "messages" not in st.session_state:
        st.session_state["messages"] = load_chat_history(cookies.get("user_email"))  # Load previous messages

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display separator after the last past message
    if cookies["display_message_separator"] == "True":
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        scroll_to_here(0, key='bottom')  # Smooth scroll to the bottom of the page
        st.session_state.scroll_down = False
        
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

    # Handle scrolling to the bottom
    if st.session_state.scroll_down:
        scroll_to_here(0, key='bottom')  # Smooth scroll to the bottom of the page
        st.session_state.scroll_down = False  # Reset the scroll state

    # Text Input Form to only trigger on Enter
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:", key="user_input")
        submit_button = st.form_submit_button("Send")
        
    if submit_button:
        trigger_bot_thinking()


def set_student_insights(user_email):
    # UI Layout
    df = get_student_progress(user_email)
    st.title("📊 Student Progress Dashboard")

    if df.empty:
        st.info("No interaction history found.")
    else:
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["date"] = df["timestamp"].dt.date

        # Sidebar Filters
        st.sidebar.header("📅 Filter Data")
        start_date = st.sidebar.date_input("Start Date", min(df["date"]))
        end_date = st.sidebar.date_input("End Date", max(df["date"]))

        df_filtered = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        # General Stats
        st.subheader("📈 Overview")
        col1, col2 = st.columns(2)
        col1.metric("Total Questions", len(df_filtered))
        col2.metric("Active Days", df_filtered["date"].nunique())

        # Topic Frequency Analysis
        st.subheader("📚 Most Discussed Topics")
        # Convert topics to lowercase before counting
        df_filtered["topic"] = df_filtered["topic"].str.lower()
        topic_counts = df_filtered["topic"].value_counts().reset_index()
        topic_counts.columns = ["Topic", "Frequency"]
        top_topics = topic_counts.head(7)  # Limit to top 7 topics
        st.bar_chart(topic_counts.set_index("Topic"))

        # Reference Materials Usage
        st.subheader("📄 Reference Material Usage")
        if df_filtered["pdfs"].notna().sum() > 0:
            pdf_counts = pd.Series(
                [pdf.split(" (Pages")[0].strip() for pdf_list in df_filtered["pdfs"].dropna() for pdf in pdf_list.split(",")]
            ).value_counts().reset_index()
            pdf_counts.columns = ["PDF Name", "Count"]
            st.bar_chart(pdf_counts.set_index("PDF Name"))
        else:
            st.write("No reference materials used.")

        # Engagement Over Time
        st.subheader("📅 Engagement Over Time")
        daily_counts = df_filtered.groupby("date").size().reset_index(name="Questions")
        st.line_chart(daily_counts.set_index("date"))

        # Display Interaction History
        st.subheader("📝 Your Question History")
        st.dataframe(df_filtered[["date", "question", "pdfs"]].rename(columns={"date": "Date", "question": "Question", "pdfs": "Referenced PDFs"}))


def trigger_bot_thinking():
    cookies["display_message_separator"] = "False"

    st.session_state["messages"].append({"role": "user", "content": st.session_state.user_input})

    # Step 2: Process the response after UI refresh
    response = send_message(st.session_state.user_input, cookies.get("user_email"))

    if response:
        st.session_state["messages"].append({"role": "assistant", "content": response})
        save_chat_history(cookies.get("user_email"), st.session_state.user_input, response)

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

if __name__ == "__main__":
    main()
