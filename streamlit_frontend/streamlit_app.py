import streamlit as st
st.set_page_config("Engi-bot", '🤖', layout="wide")

from streamlit_scroll_to_top import scroll_to_here
import pandas as pd
from streamlit_cookies_manager import EncryptedCookieManager

from streamlit_utils import *

# Generate a strong secret key for your application
SECRET_KEY = "your_strong_secret_key_here" # ??

#@st.cache_resource
def get_cookie_manager():
    return EncryptedCookieManager(prefix="chatbot_app_", password=SECRET_KEY)

cookies = get_cookie_manager()

# Wait until cookies are ready
if not cookies.ready():
    #st.warning("Initializing session... Please wait.")
    st.stop()  # Stop execution until cookies are available


# Streamlit UI
def main():

    #if "scroll_down" not in st.session_state:
    st.session_state["scroll_down"] = True
    
    if "display_message_separator" not in cookies:
        cookies["display_message_separator"] = "True"
    
    if "input_disabled" not in st.session_state:
        st.session_state.input_disabled = "False"

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Sidebar for logout
    with st.sidebar:
        st.title("Engi-bot")
        if cookies.get("logged_in") == "True":
            user_email = cookies.get("user_email")
            role = get_user_role(user_email)
            user=fetch_user(user_email)
            if user:
                if role == "Student":
                    st.write(f"Hello **{user.get('name')}**!")
                else:
                    st.write(f"Hello Professor **{user.get('name')}**!")
                #st.write(f"Logged in as **{user_email}**")
            
            if st.button("Logout"):
                logout()
            
            if role == "Student":
                if not is_authorized(user_email):
                    return
                else:
                    set_student_insights(user_email)
            elif role == "Teacher":
                set_teacher_insights(user_email) 

        else:
            st.info("Please log in or register.")

    if cookies.get("logged_in") != "True":
        auth_tabs()
    else:
        chat_interface()

def auth_tabs():
    st.title("🔑 Authentication")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        login_form()
    with tab2:
        register_form()

def chat_interface():
    st.title("💬 Chat with EngiBot")
    user_role = get_user_role(cookies.get("user_email"))

    if user_role == "Teacher":

        if not st.session_state.get("bot_thinking", False):
            teacher_classes = fetch_teacher_classes(cookies.get("user_email"))
            if not teacher_classes:
                st.info(f"No classes found for teacher.")
                return 
            df_classes = pd.DataFrame(teacher_classes, columns=["id", "code", "number", "course"])

            if df_classes.empty:
                st.info("No assigned classes found.")
                return

            # Create a unique identifier for each class by concatenating name and number
            df_classes["class_identifier"] = df_classes["code"] + "-" + df_classes["number"]
            # add all possible classes names to the class_identifier column
            class_counts = df_classes["code"].value_counts().reset_index()
            class_counts.columns = ["code", "count"]
            for i, row in class_counts.iterrows():
                if row["count"] > 1:
                    new_row = pd.DataFrame({"class_identifier": [row["code"] + "-All"], "code": [row["code"]], "number": ["-1"]})
                    df_classes = pd.concat([df_classes, new_row], ignore_index=True)

            # check if there is only one class for the teacher
            if len(class_counts) > 1:
                # Add an "all" class to the list
                all_class_row = pd.DataFrame({"class_identifier": ["All"], "code": ["All"], "number": ["-1"]})
                df_classes = pd.concat([df_classes, all_class_row], ignore_index=True)

            # Sidebar: Select class
            selected_class_identifier = st.selectbox("📚 Select a Class", df_classes["class_identifier"].unique(), key="selected_class")
            st.session_state["class_identifier"] = selected_class_identifier

            # Display insight buttons only if a class is selected
            if selected_class_identifier:

                # Extract the selected class code and number
                selected_class_row = df_classes[df_classes["class_identifier"] == selected_class_identifier].iloc[0]
                selected_class_code = selected_class_row["code"]
                selected_class_number = selected_class_row["number"]

                st.session_state["selected_class_code"] = selected_class_code
                st.session_state["selected_class_number"] = selected_class_number

                # Populate buttons for insights
                if not st.session_state.get("buttons", False):
                    _, buttons = send_message("buttons for insights", cookies.get("user_email"))
                    st.session_state["buttons"] = buttons

                # Display buttons
                if st.session_state.get("buttons"):
                    buttons = st.session_state["buttons"]
                    # save buttons in session state
                    cols = st.columns(len(buttons))
                    for i, btn in enumerate(buttons):
                        if cols[i].button(btn["title"]):
                            st.session_state["selected_button_payload"] = btn["payload"]
                            process_bot_response(btn["payload"], selected_class_code, selected_class_number)
                            return
    
        if st.session_state["messages"]:
            with st.chat_message(st.session_state["messages"][-1]["role"]):
                st.markdown(st.session_state["messages"][-1]["content"])

        # add an input form to get the custom query from the teacher
        with st.form(key="custom_query_form", clear_on_submit=True):
            custom_teacher_query = st.text_input("Type your question:", key="custom_teacher_query")
            submit_button = st.form_submit_button("Send")
        if submit_button and custom_teacher_query.strip():
            # Append user message to the chat
            st.session_state["messages"].append({"role": "user", "content": custom_teacher_query})
            process_bot_response("/custom_teacher_query", st.session_state["selected_class_code"], st.session_state["selected_class_number"], custom_teacher_query)
            st.rerun()
                            
    else:
        # Load previous messages
        if st.session_state["messages"] == []:
            st.session_state["messages"] = load_chat_history(cookies.get("user_email"))

        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Display separator for new messages
        if cookies.get("display_message_separator") == "True":
            display_message_separator()      

        # Handle scrolling to the bottom
        if st.session_state.scroll_down:
            scroll_to_here(0, key='bottom')  # Smooth scroll to the bottom of the page
            st.session_state.scroll_down = False  # Reset the scroll state

        # ❌ Don't show form if bot is thinking
        if not st.session_state.get("bot_thinking", False):
            st.markdown(
                """
                <style>
                    div[data-testid="stForm"] {
                        margin-bottom: max(-20vh, -6em) !important;  /* Reduce bottom spacing */
                    }
                </style>
                """,
                unsafe_allow_html=True
            )

            # show input form
            with st.form(key="input_form", clear_on_submit=True):
                user_input = st.text_input("Type your message:", key="user_input")
                submit_button = st.form_submit_button("Send")
            # 🚀 Trigger bot thinking when user submits a message
            if submit_button and user_input.strip():
                trigger_bot_thinking(user_input)

        # 🛠️ Check if bot is thinking and process response BEFORE displaying UI
        if st.session_state.get("bot_thinking", False):
            process_bot_response(st.session_state["messages"][-1]["content"])
            return  # Prevents UI from rendering mid-processing
                

def trigger_bot_thinking(user_input):
    cookies["display_message_separator"] = "False"

    # Append user message to the chat
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Set bot_thinking to True & rerun
    st.session_state["bot_thinking"] = True
    st.rerun()

def process_bot_response(trigger, selected_class_name=None, selected_class_number=None, teacher_question=None):
    """Handles bot response automatically when bot_thinking is True."""

    user_email = cookies.get("user_email")
    user_role = get_user_role(user_email)

    if user_role == "Teacher":
        response, _ = send_message(trigger, user_email, selected_class_name, selected_class_number, teacher_question)

        if response:
            st.session_state["messages"].append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        else:
            error_message = "🤖 Sorry, I didn't understand that."
            st.session_state["messages"].append({"role": "assistant", "content": error_message})

            with st.chat_message("assistant"):
                st.markdown(error_message)

        # clear the selected button payload
        st.session_state["teacher_message_sent"] = False  # Allow re-triggering
    else:
        with st.status("Thinking... 🤖", expanded=True) as status:
            response, _ = send_message(trigger, user_email)

            if response:
                st.session_state["messages"].append({"role": "assistant", "content": response})
                save_message_history(user_email, {"question": trigger, "response": response})

                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                error_message = "🤖 Sorry, I didn't understand that."
                st.session_state["messages"].append({"role": "assistant", "content": error_message})

                with st.chat_message("assistant"):
                    st.markdown(error_message)

    # ✅ Reset `bot_thinking` so input appears again
    st.session_state["bot_thinking"] = False
    st.rerun()
    

def set_student_insights(student_email):
    # UI Layout
    student_progress = fetch_student_progress(student_email)
    if student_progress == {}:  # No progress found
        return
    df = pd.DataFrame(student_progress, columns=["class_id", "question", "response", "topic", "pdfs", "timestamp"])

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
        st.bar_chart(top_topics.set_index("Topic"))

        # Reference Materials Usage
        st.subheader("📄 Reference Material Usage")
        # drop empty pdfs
        df_filtered_pdfs = df_filtered[df_filtered["pdfs"].apply(lambda x: bool(x) and x != "{}")]
        if not df_filtered_pdfs.empty:
            pdf_list = []
            for pdfs in df_filtered_pdfs["pdfs"].dropna():
                for pdf in pdfs.split(","):
                    pdf_list.append(pdf.split(" (Pages")[0].strip())

            # count the frequency of each pdf
            pdf_counts = pd.Series(pdf_list).value_counts().reset_index()
            pdf_counts.columns = ["PDF Name", "Count"]

            # order by count
            pdf_counts = pdf_counts.sort_values(by="Count", ascending=False) 
            # show only top 5 pdfs
            top_pdfs = pdf_counts.head(5)

            # display bar chart
            st.bar_chart(top_pdfs.set_index("PDF Name"))
        else:
            st.write("No reference materials used.")

        # Engagement Over Time
        st.subheader("📅 Engagement Over Time")
        daily_counts = df_filtered.groupby("date").size().reset_index(name="Questions")
        st.line_chart(daily_counts.set_index("date"))

        # Display Interaction History
        st.subheader("📝 Your Question History")
        st.dataframe(df_filtered[["date", "question", "pdfs"]].rename(columns={"date": "Date", "question": "Question", "pdfs": "Referenced PDFs"}))

def set_teacher_insights(user_email):
    st.title("📊 Class Engagement Dashboard")

    # Fetch teacher's classes
    teacher_classes = fetch_teacher_classes(user_email)
    if not teacher_classes:
        st.info(f"No classes found for teacher: {user_email}")
        return 
    df_classes = pd.DataFrame(teacher_classes, columns=["id", "code", "number", "course"])
    
    # Sidebar: Select class
    selected_class_code = st.sidebar.selectbox("Select a Class", df_classes["code"].unique())
    st.session_state["selected_class_code"] = selected_class_code

    # display available class numbers and let the teacher select one
    st.sidebar.write("Class Numbers:")
    class_numbers = df_classes[df_classes["code"] == selected_class_code]["number"].values
    selected_class_number = st.sidebar.selectbox("Select a Class Number", class_numbers)
    st.session_state["selected_class_number"] = selected_class_number

    # get id of the current class
    classes = fetch_classes()
    class_id = None
    for class_ in classes:
        if class_.get("code") == selected_class_code and class_.get("number") == selected_class_number:
            class_id = class_.get("id")
            break

    # Fetch student progress for selected class
    class_progress = fetch_class_progress(class_id)
    if class_progress == []:
        st.info("No student interactions recorded.")
        return

    # Create a DataFrame from the class progress
    df = pd.DataFrame(class_progress, columns=["student_up", "question", "response", "topic", "pdfs", "timestamp"])
    
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["Date"] = df["timestamp"].dt.date

    # Sidebar Filters
    st.sidebar.header("📅 Filter Data")
    start_date = st.sidebar.date_input("Start Date", min(df["Date"]))
    end_date = st.sidebar.date_input("End Date", max(df["Date"]))

    df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    # General Stats
    st.subheader("📈 Overview")
    col1, col2 = st.columns(2)
    col1.metric("Total Questions", len(df_filtered))
    col2.metric("Unique Students", df_filtered["student_up"].nunique())

    # Topic Analysis
    st.subheader("📚 Most Discussed Topics")
    df_filtered["topic"] = df_filtered["topic"].str.lower()
    topic_counts = df_filtered["topic"].value_counts().reset_index()
    topic_counts.columns = ["topic", "Frequency"]
    st.bar_chart(topic_counts.set_index("topic"))

    # Reference Materials Usage
    st.subheader("📄 Reference Material Usage")
    # drop empty pdfs
    df_filtered_pdfs = df_filtered[df_filtered["pdfs"].apply(lambda x: bool(x) and x != "{}")]
    if not df_filtered_pdfs.empty:
        pdf_list = []
        for pdfs in df_filtered_pdfs["pdfs"].dropna():
            for pdf in pdfs.split(","):
                pdf_list.append(pdf.split(" (Pages")[0].strip())

        # count the frequency of each pdf
        pdf_counts = pd.Series(pdf_list).value_counts().reset_index()
        pdf_counts.columns = ["PDF Name", "Count"]

        # order by count
        pdf_counts = pdf_counts.sort_values(by="Count", ascending=False) 
        # show only top 5 pdfs
        top_pdfs = pdf_counts.head(5)

        # display bar chart
        st.bar_chart(top_pdfs.set_index("PDF Name"))
    else:
        st.write("No reference materials used.")

    # Engagement Over Time
    st.subheader("📅 Engagement Over Time")
    daily_counts = df_filtered.groupby("Date").size().reset_index(name="questions")
    st.line_chart(daily_counts.set_index("Date"))

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
        
def login_form():
    st.subheader("Login to Your Account")
    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔒 Password", type="password", key="login_password")

    if st.button("Login"):
        if not is_valid_email(email):
            st.error("❌ Invalid email format!")
            return
        hashed_password = hash_password(password)
        user = authenticate_user(email, hashed_password)
        if user:
            cookies["logged_in"] = "True"
            cookies["user_email"] = email
            cookies.save()
            #st.success("✅ Login successful! Your previous chat history has been loaded.")
            st.rerun()
        else:
            st.error("❌ Invalid email or password!")
            
def logout():
    st.session_state.clear()
    cookies["logged_in"] = "False"
    cookies["user_email"] = ""
    cookies["display_message_separator"] = "True"
    cookies.save()
    sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()
