import streamlit as st
from assistant_api import (
    createAssistant, saveFileOpenAI, startAssistantThread, runAssistant,
    checkRunStatus, retrieveThread, addMessageToThread
)
import time

def display_thread_messages(thread_messages):
    """Display messages from the thread."""
    for message in thread_messages:
        role = 'User' if message['role'] == 'user' else 'Assistant'
        st.write(f"{role} Message: {message['content']}")

def process_run(thread_id, assistant_id):
    """Process the thread and continuously check the status until completion."""
    run_id = runAssistant(thread_id, assistant_id)
    status = 'running'
    while status != 'completed':
        with st.spinner('Waiting for assistant response...'):
            time.sleep(20)
            status = checkRunStatus(thread_id, run_id)
    thread_messages = retrieveThread(thread_id)
    display_thread_messages(thread_messages)

def main():
    st.title("🚀 SealCoin Assistant V2")

    assistant_id = st.text_input("Enter the Assistant ID if known:")
    thread_id = st.text_input("Enter existing Thread ID to continue the conversation:")

    if st.button('Load Conversation'):
        if thread_id:
            thread_messages = retrieveThread(thread_id)
            if thread_messages:
                display_thread_messages(thread_messages)
                st.session_state['thread_id'] = thread_id  # Ensure thread ID is stored in session state
                st.session_state['assistant_id'] = assistant_id
            else:
                st.error("Failed to load messages or no messages in the thread.")
        else:
            st.error("Please provide a Thread ID.")

    if st.button('Initialize New Assistant'):
        title = st.text_input("Enter the title for a new Assistant")
        initiation = st.text_input("Enter the first question to start a new conversation")
        uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True)
        if uploaded_files and title and initiation:
            file_ids = [saveFileOpenAI(file.getvalue()) for file in uploaded_files]
            assistant_id, _ = createAssistant(file_ids, title)
            thread_id = startAssistantThread(initiation, assistant_id)
            st.session_state.update({
                'assistant_initialized': True,
                'thread_id': thread_id,
                'assistant_id': assistant_id
            })
            st.write("New assistant and thread initialized.")

    if 'thread_id' in st.session_state:
        follow_up = st.text_input("Enter your follow-up question")
        if st.button("Send Follow-up"):
            success = addMessageToThread(st.session_state['thread_id'], follow_up)
            if success:
                st.success("Message added to the conversation.")
                process_run(st.session_state['thread_id'], st.session_state['assistant_id'])
            else:
                st.error("Failed to add message to the conversation.")

if __name__ == "__main__":
    main()