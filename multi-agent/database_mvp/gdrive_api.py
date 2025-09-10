import io
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import pandas as pd

# Constants
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(),'database_mvp','orion-431410-ee3221a6bafe.json')
SCOPES = ['https://www.googleapis.com/auth/drive']
MAIN_MESSAGES_ID = '1ymyv3IOeBX5rCnjSIRGGeEfAmBzmcZG0'
AGENT_CONVERSATIONS_ID = '16Jdb6qXJG7rRO0LKrwTN6t2XgwVIXv-C'

# Initialize Google Drive service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

def download_file(service, file_id, local_filename):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    with io.open(local_filename, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())

def upload_file(service, file_id, local_filename):
    file_metadata = {'name': local_filename.split('\\')[-1]}
    media = MediaFileUpload(local_filename, mimetype='text/csv')
    service.files().update(fileId=file_id, body=file_metadata,
                           media_body=media, fields='id').execute()

def backup_db():
    # Upload files to Google Drive
    upload_file(service, MAIN_MESSAGES_ID, os.path.join(os.getcwd(),'database_mvp','MainMessages.csv'))
    upload_file(service, AGENT_CONVERSATIONS_ID, os.path.join(os.getcwd(),'database_mvp','AgentConversations.csv'))

def load_db():
    # Download files from Google Drive
    download_file(service, MAIN_MESSAGES_ID, os.path.join(os.getcwd(),'database_mvp','MainMessages.csv'))
    download_file(service, AGENT_CONVERSATIONS_ID, os.path.join(os.getcwd(),'database_mvp','AgentConversations.csv'))

def get_user_messages(user_id):
    # read the user messages from the MainMessages.csv file to pandas dataframe
    messages_df = pd.read_csv(os.path.join(os.getcwd(),'database_mvp','MainMessages.csv'))
    # convert the 'timestamp' column to datetime
    messages_df['timestamp'] = pd.to_datetime(messages_df['timestamp'])
    # get all rows where values from column 'user_id' match the user_id
    rows = messages_df[messages_df['user_id'] == user_id]
    # sort rows by timestamp and store in a list of dictionaries
    # each dict should contain {'message': #value_of_column_message_content,"role": ['user'/'agent'][#value_of_bool_column_'is_user_message']}
    messages = rows.sort_values(by='timestamp').apply(lambda row: {'role': 'user' if row['is_user_message'] else 'assistant', 'content': row['message_content']}, axis=1).tolist()
    return messages

def save_main_message(user_id,message_content,is_user_message):
    # read the MainMessages.csv file to pandas dataframe
    messages_df = pd.read_csv(os.path.join(os.getcwd(),'database_mvp','MainMessages.csv'))
    # identify the last message_id so you can create new one by incrementing it by 1
    message_id = messages_df['message_id'].max() + 1
    # get current timestamp
    timestamp = pd.Timestamp.now()
    # create a new row with the new message
    new_row = pd.DataFrame({
        'message_id': [message_id], 
        'user_id': [user_id], 
        'message_content': [message_content], 
        'timestamp': [timestamp], 
        'is_user_message': [is_user_message]
    })
    # append the new row to the dataframe
    messages_df = pd.concat([messages_df, new_row], ignore_index=True)
    # save the updated dataframe to the MainMessages.csv file
    messages_df.to_csv(os.path.join(os.getcwd(),'database_mvp','MainMessages.csv'), index=False)
    return message_id
    
def save_agent_conversation(message_id,messages,timestamps):
    # read the AgentConversations.csv file to pandas dataframe
    agent_df = pd.read_csv(os.path.join(os.getcwd(),'database_mvp','AgentConversations.csv'))
    # identify the last thread_message_id so you can create new one by incrementing it by 1
    last_thread_message_id = agent_df['thread_message_id'].max()
    # Messages is a list of dicts in format {'role': #agent_name, 'content': #message_content},
    # timestamps is a list of timestamps with matching length
    # Extend df with new rows
    new_rows = [{'thread_message_id': last_thread_message_id + i + 1,
                 'message_id': message_id,
                 'agent_name': messages[i]['role'],
                 'message_content': messages[i]['content'],
                 'timestamp': timestamps[i]} for i in range(len(messages))]
    
    # Create a DataFrame from the new rows
    new_rows_df = pd.DataFrame(new_rows)
    # Append the new rows to the DataFrame using concat
    agent_df = pd.concat([agent_df, new_rows_df], ignore_index=True)
    
    # Save the updated DataFrame to the AgentConversations.csv file
    agent_df.to_csv(os.path.join(os.getcwd(),'database_mvp','AgentConversations.csv'), index=False)


# list all the imports for the future
# from . import backup_db, load_db, get_user_messages, save_main_message, save_agent_conversation
# Optional: Uncomment these lines to test the functions
# backup_db()
# load_db()
