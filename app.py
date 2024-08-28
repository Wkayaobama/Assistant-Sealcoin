import streamlit as st
from assistant_api import (
    createAssistant, saveFileOpenAI, startAssistantThread, runAssistant,
    checkRunStatus, retrieveThread, addMessageToThread,save_thread_details,load_thread_details
)
import time

def display_thread_messages(thread_messages):
    """Display messages from the thread based on visibility state."""
    if st.session_state.get('show_messages', True):
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
    st.title("🪙 SealCoin Assistant")

    # Load thread details from file
    thread_details = load_thread_details()
    thread_id = ""
    assistant_id = ""
    if thread_details:
        thread_id = thread_details.get('thread_id', '')
        assistant_id = thread_details.get('assistant_id', '')

    # Input fields prepopulated with data from JSON
    thread_id = st.text_input("Enter existing Thread ID to continue the conversation:", value=thread_id)
    assistant_id = st.text_input("Enter the Assistant ID if known:", value=assistant_id)

    if st.button('Load Conversation'):
        if thread_id:
            thread_messages = retrieveThread(thread_id)
            if thread_messages:
                display_thread_messages(thread_messages)
                st.session_state['thread_id'] = thread_id
                st.session_state['assistant_id'] = assistant_id
            else:
                st.error("Failed to load messages or no messages in the thread.")
        else:
            st.error("Please provide a Thread ID.")

    if st.button('Initialize New Assistant'):
        title = st.text_input("Enter the title for a new Assistant", key='new_title')
        initiation = st.text_input("Enter the first question to start a new conversation", key='new_initiation')
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
            # Save new thread details
            save_thread_details(thread_id, assistant_id)

   
    if 'thread_id' in st.session_state:
        follow_up = st.text_input("Enter your follow-up question")
        if st.button("Send Follow-up"):
            success = addMessageToThread(st.session_state['thread_id'], follow_up)
            if success:
                st.success("Message added to the conversation.")
                process_run(st.session_state['thread_id'], st.session_state['assistant_id'])
            else:
                st.error("Failed to add message to the conversation.")
        st.checkbox('Show Messages', value=st.session_state.get('show_messages', True), key='show_messages')

    if st.button('Clear Conversation'):
        st.session_state.pop('thread_id', None)
        st.session_state.pop('assistant_id', None)
        save_thread_details(None, None)  # Clear the file
        st.write("Conversation cleared.")

if __name__ == "__main__":
    main()