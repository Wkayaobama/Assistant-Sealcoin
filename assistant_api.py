from openai import OpenAI
import config
import os
import time
import json
import tempfile
import shutil

client = OpenAI(api_key=config.API_KEY)
def createAssistant(file_ids, title):
    #Create the OpenAI Client Instance
    client = OpenAI(api_key=config.API_KEY)

    #GET Instructions saved in the Settings.py File (We save the instructions there for easy access when modifying)
    instructions = """
    You are a helpful assistant. Use your knowledge base to answer user questions.
    """

    #The GPT Model for the Assistant (This can also be updated in the settings )
    model = "gpt-4-turbo"

    #Only Retireval Tool is relevant for our use case
    tools = [{"type": "file_search"}]

    ##CREATE VECTOR STORE
    vector_store = client.beta.vector_stores.create(name=title,file_ids=file_ids)
    tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}}

    #Create the Assistant
    assistant = client.beta.assistants.create(
    name=title,
    instructions=instructions,
    model=model,
    tools=tools,
    tool_resources=tool_resources
    )

    #Return the Assistant ID
    return assistant.id,vector_store.id



def saveFileOpenAI(location):
    client = OpenAI(api_key=config.API_KEY)
    file_id = None
    try:
        with open(location, "rb") as file:
            # Send File to OpenAI
            file_response = client.files.create(file=file, purpose='assistants')
            file_id = file_response.id
    finally:
        # Ensure the file is not in use and is deleted properly
        os.remove(location)
    return file_id



def startAssistantThread(prompt,vector_id):
    #Initiate Messages
    messages = [{"role": "user", "content": prompt}]
    #Create the OpenAI Client
    client = OpenAI(api_key=config.API_KEY)
    #Create the Thread
    tool_resources = {"file_search": {"vector_store_ids": [vector_id]}}
    thread = client.beta.threads.create(messages=messages,tool_resources=tool_resources)

    return thread.id



def runAssistant(thread_id, assistant_id):
    #Create the OpenAI Client
    client = OpenAI(api_key=config.API_KEY)
    run = client.beta.threads.runs.create(thread_id=thread_id,assistant_id=assistant_id)
    return run.id



def checkRunStatus(thread_id, run_id):
    client = OpenAI(api_key=config.API_KEY)
    run = client.beta.threads.runs.retrieve(thread_id=thread_id,run_id=run_id)
    return run.status



def retrieveThread(thread_id):
    client = OpenAI(api_key=config.API_KEY)
    thread_messages = client.beta.threads.messages.list(thread_id)
    list_messages = thread_messages.data
    thread_messages = []
    for message in list_messages:
        obj = {}
        obj['content'] = message.content[0].text.value
        obj['role'] = message.role
        thread_messages.append(obj)
    return thread_messages[::-1]



def addMessageToThread(thread_id, prompt):
    """Adds a message to an existing thread and returns True if successful."""
    try:
        client = OpenAI(api_key=config.API_KEY)
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)
        return True
    except Exception as e:
        print(f"Error adding message to thread: {e}")
        return False



## Update assistant

def update_assistant(assistant_id, new_name, new_description):
    """Updates the OpenAI Assistant configuration."""
    try:
        updated_assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            name=new_name,
            description=new_description,
            model="gpt-4-turbo",  # Assuming you want to keep/update the model as well
        )
        return updated_assistant
    except Exception as e:
        print(f"Failed to update assistant: {str(e)}")
        return None

def create_and_run_thread(assistant_id, user_prompt):
    """Creates a thread and runs the OpenAI Assistant."""
    try:
        chat = client.beta.threads.create(
            messages=[{"role": "user", "content": user_prompt}]
        )
        run = client.beta.threads.runs.create(thread_id=chat.id, assistant_id=assistant_id)
        print(f"Run Created: {run.id}")

        # Wait for the run to complete
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=chat.id, run_id=run.id)
            print(f"Run Status: {run.status}")
            time.sleep(0.5)  # Adjust as necessary

        if run.status == "completed":
            print("Run Completed!")

        # Retrieve and print the latest message from the assistant
        message_response = client.beta.threads.messages.list(thread_id=chat.id)
        messages = message_response.data
        if messages and messages[-1].role == 'assistant':
            print("Response:", messages[-1].content[0].text.value)
        else:
            print("No response found.")
    except Exception as e:
        print(f"Error during thread creation or execution: {str(e)}")


import json

def save_thread_details(thread_id, assistant_id):
    """Atomically save thread and assistant details to a JSON file."""
    temp_fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, 'w') as tmp_file:
            json.dump({"thread_id": thread_id, "assistant_id": assistant_id}, tmp_file, indent=4)
        shutil.move(temp_path, "thread_details.json")  # Atomically replace the old file
    except Exception as e:
        os.unlink(temp_path)
        print(f"Failed to save thread details: {e}")

def load_thread_details():
    """Load thread and assistant details from a JSON file with retries for robustness."""
    retry_attempts = 3
    while retry_attempts > 0:
        try:
            with open("thread_details.json", "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error decoding JSON from the file, retrying...")
            retry_attempts -= 1
        except FileNotFoundError:
            print("The file doesn't exist.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    print("Failed to load thread details after several attempts.")
    return None



# Example usage
#thread_id = "thread_XoO7X1cBQHyMuj9qcj2rtXms"
#assistant_id = "asst_xjtt9zGAk6Rszk6UQ3HN1Cfr"


# Example usage:
""" assistant_id = "asst_xjtt9zGAk6Rszk6UQ3HN1Cfr"
new_name = "SEALCOINV3"
new_description = "Hi How Are You?" """

# Update Assistant Configuration
# update_assistant(assistant_id, new_name, new_description)

# Create and Run Thread
#user_prompt = "tell me about the best jobs in AI"
#create_and_run_thread(assistant_id, user_prompt)