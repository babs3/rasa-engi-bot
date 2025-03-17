import streamlit as st
import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor

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
    
    # Authentication
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_email"] = ""
    
    if not st.session_state["logged_in"]:
        login_form()
    else:
        chat_interface()

def login_form():
    st.title("Login to Chatbot")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate_user(email, password):
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = email
            st.rerun()
        else:
            st.error("Invalid credentials!")

# Simulated authentication (replace with a real user database check)
def authenticate_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM "user" WHERE email = %s', (email,)) # AND password = %s', (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

def chat_interface():
    st.title("Chat with Rasa Bot")
    st.write(f"Logged in as: {st.session_state['user_email']}")
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    # Display previous messages
    for message in st.session_state["messages"]:
        st.markdown(message)
    
    user_input = st.text_input("You:", "")
    if st.button("Send") and user_input:
        response = send_message(user_input, st.session_state["user_email"])
        if response:
            st.session_state["messages"].append(f"**You:** {user_input}")
            st.session_state["messages"].append(f"**Bot:** {response}")
        st.rerun()

def send_message(user_input, user_email):
    url = "http://rasa:5005/webhooks/rest/webhook"
    payload = {
        "sender": user_email,  # Send user email as sender ID
        "message": user_input,
        "metadata": {"user_email": user_email}  # Pass metadata to Rasa
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        messages = response.json()
        
        if messages:
            bot_reply = messages[0]["text"]
            save_chat_history(user_email, user_input, bot_reply)
            return bot_reply
        return "Sorry, I didn't understand that."
    except requests.RequestException as e:
        st.error(f"Error connecting to Rasa: {e}")
        return None

def save_chat_history(user_email, user_message, bot_response):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch user_id from user table
    cur.execute('SELECT id FROM "user" WHERE email = %s', (user_email,))
    user = cur.fetchone()
    
    if user:
        user_id = user['id']
        cur.execute(
            "INSERT INTO user_history (user_id, user_message, bot_response, timestamp) VALUES (%s, %s, %s, NOW())",
            (user_id, user_message, bot_response)
        )
        conn.commit()
    else:
        print(f"User with email {user_email} not found.")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
