import streamlit as st
st.set_page_config("Engi-bot", '🤖', layout="wide")

from streamlit_scroll_to_top import scroll_to_here
import pandas as pd

from streamlit_utils import *


# Streamlit UI
def main():
    # Sidebar for logout
    with st.sidebar:
        st.title("Engi-bot")
        if cookies.get("logged_in") == "True":
            user_email = cookies.get("user_email")
            st.write(f"Logged in as **{user_email}**")
            
            if st.button("Logout"):
                logout()

            # get user role
            role = get_user_role(user_email)
            if role == "Student":
                set_student_insights(user_email)
            else: # role == "Teacher"
                set_teacher_insights(user_email) 

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

    if user_role == "Student":

        if "messages" not in st.session_state:
            st.session_state["messages"] = load_chat_history(cookies.get("user_email"))  # Load previous messages

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

    if user_role == "Teacher":
        buttons = []

        if not st.session_state.get("bot_thinking", False):

            if st.session_state.get("selected_button_payload") == "/custom_teacher_query":
                # add an input form to get the custom query from the teacher
                with st.form(key="custom_query_form", clear_on_submit=True):
                    custom_teacher_query = st.text_input("Type your question:", key="custom_teacher_query")
                    submit_button = st.form_submit_button("Send")
                if submit_button and custom_teacher_query.strip():
                    st.info("triggering bot thinking...")
                    sleep(2)
                    trigger_bot_thinking(custom_teacher_query)
                    st.rerun()

            # Fetch available classes - columns=["id", "course", "name", "number", "students"])
            # available classes name and number like GEE 101, GEE 102, etc.
            df_classes = get_teacher_classes(cookies.get("user_email"))

            if df_classes.empty:
                st.info("No assigned classes found.")
                return

            # Create a unique identifier for each class by concatenating name and number
            df_classes["class_identifier"] = df_classes["name"] + "-" + df_classes["number"]
            # get all the unique class names to a list
            class_names = df_classes["name"].unique()
            # add all possible classes names to the class_identifier column
            for class_name in class_names:
                new_row = pd.DataFrame({"class_identifier": [class_name + "-All"], "name": [class_name], "number": ["-1"]})
                df_classes = pd.concat([df_classes, new_row], ignore_index=True)
            # Add an "all" class to the list
            all_class_row = pd.DataFrame({"class_identifier": ["All"], "name": ["All"], "number": ["-1"]})
            df_classes = pd.concat([df_classes, all_class_row], ignore_index=True)

            # Sidebar: Select class
            selected_class_identifier = st.selectbox("📚 Select a Class", df_classes["class_identifier"].unique(), key="selected_class")
            st.session_state["class_identifier"] = selected_class_identifier

            # Display insight buttons only if a class is selected
            if selected_class_identifier:

                # Extract the selected class name and number
                selected_class_row = df_classes[df_classes["class_identifier"] == selected_class_identifier].iloc[0]
                selected_class_name = selected_class_row["name"]
                selected_class_number = selected_class_row["number"]

                # Populate buttons for insights
                if not st.session_state.get("buttons", False):
                    response, buttons = send_message("buttons for insights", cookies.get("user_email"))
                    st.session_state["buttons"] = buttons

                # Display buttons
                if st.session_state.get("buttons"):
                    buttons = st.session_state["buttons"]
                    # save buttons in session state
                    cols = st.columns(len(buttons))
                    for i, btn in enumerate(buttons):
                        if cols[i].button(btn["title"]):
                            # save the selected button payload in session state
                            st.session_state["selected_button_payload"] = btn["payload"]
                            # save the selected class name and number in session state
                            st.session_state["selected_class_name"] = selected_class_name
                            st.session_state["selected_class_number"] = selected_class_number

                            if btn["payload"] != "/custom_teacher_query":
                                process_teacher_bot_response(btn["payload"], selected_class_name, selected_class_number)
                            else:
                                st.info("🚧 Custom queries are under construction.")
                                st.rerun()
                            return
        
        # 🛠️ Check if bot is thinking and process response BEFORE displaying UI
        elif st.session_state.get("bot_thinking", False):
            process_teacher_bot_response(st.session_state["selected_button_payload"], st.session_state["selected_class_name"], st.session_state["selected_class_number"])
            return  # Prevents UI from rendering mid-processing
                            
    else:
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
        
    if user_role == "Teacher":
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

        # display only last message and the message before that if its from the user
        if st.session_state["messages"]:
            if len(st.session_state["messages"]) > 1:
                if st.session_state["messages"][-2]["role"] == "user":
                    with st.chat_message(st.session_state["messages"][-2]["role"]):
                        st.markdown(st.session_state["messages"][-2]["content"])
            with st.chat_message(st.session_state["messages"][-1]["role"]):
                st.markdown(st.session_state["messages"][-1]["content"])

def trigger_bot_thinking(user_input):
    cookies["display_message_separator"] = "False"
    st.info("🤖 Thinking...")
    sleep(2)

    # Append user message to the chat
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Set bot_thinking to True & rerun
    st.session_state["bot_thinking"] = True
    st.rerun()

def process_teacher_bot_response(btn_payload, selected_class_name=None, selected_class_number=None):
    user_email = cookies.get("user_email")
    response, _ = send_message(btn_payload, user_email, selected_class_name, selected_class_number)
    st.info(btn_payload)
    st.info(response)
    sleep(3)

    # use st.status if btn_payload is /custom_teacher_query
    if btn_payload == "/custom_teacher_query":
        with st.status("Thinking... 🤖", expanded=True) as status:
            if response:
                st.session_state["messages"].append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                error_message = "🤖 Sorry, I didn't understand that."
                st.session_state["messages"].append({"role": "assistant", "content": error_message})

                with st.chat_message("assistant"):
                    st.markdown(error_message)
    else:
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
    st.session_state["selected_button_payload"] = None 
    st.session_state["teacher_message_sent"] = False  # Allow re-triggering
    # ✅ Reset `bot_thinking` so input appears again
    st.session_state["bot_thinking"] = False
    st.rerun()

def process_bot_response(user_input):
    """Handles bot response automatically when bot_thinking is True."""
    user_email = cookies.get("user_email")

    with st.status("Thinking... 🤖", expanded=True) as status:
        response, btns = send_message(user_input, user_email)

        if response:
            st.session_state["messages"].append({"role": "assistant", "content": response})
            save_chat_history(user_email, user_input, response)

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
            #st.info(pdf_list)

            # count the frequency of each pdf
            pdf_counts = pd.Series(pdf_list).value_counts().reset_index()
            pdf_counts.columns = ["PDF Name", "Count"]

            # order by count
            pdf_counts = pdf_counts.sort_values(by="Count", ascending=False) 
            #st.info(pdf_counts)
            # show only top 5 pdfs
            top_pdfs = pdf_counts.head(5)
            #st.info(top_pdfs)

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
    df_classes = get_teacher_classes(user_email)

    if df_classes.empty:
        st.info("No assigned classes found.")
        return

    # Sidebar: Select class
    selected_class = st.sidebar.selectbox("Select a Class", df_classes["name"].unique())
    st.session_state["class_name"] = selected_class

    # display available class numbers and let the teacher select one
    st.sidebar.write("Class Numbers:")
    class_numbers = df_classes[df_classes["name"] == selected_class]["number"].values
    selected_class_number = st.sidebar.selectbox("Select a Class Number", class_numbers)
    st.session_state["class_number"] = selected_class_number

    # Fetch student progress for selected class
    df = get_class_progress(selected_class, selected_class_number)

    if df.empty:
        st.info("No student interactions recorded.")
        return

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
    col2.metric("Unique Students", df_filtered["student_up_id"].nunique())

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
        #st.info(pdf_list)

        # count the frequency of each pdf
        pdf_counts = pd.Series(pdf_list).value_counts().reset_index()
        pdf_counts.columns = ["PDF Name", "Count"]

        # order by count
        pdf_counts = pdf_counts.sort_values(by="Count", ascending=False) 
        #st.info(pdf_counts)
        # show only top 5 pdfs
        top_pdfs = pdf_counts.head(5)
        #st.info(top_pdfs)

        # display bar chart
        st.bar_chart(top_pdfs.set_index("PDF Name"))
    else:
        st.write("No reference materials used.")

    # Engagement Over Time
    st.subheader("📅 Engagement Over Time")
    daily_counts = df_filtered.groupby("Date").size().reset_index(name="questions")
    st.line_chart(daily_counts.set_index("Date"))

if __name__ == "__main__":
    main()
