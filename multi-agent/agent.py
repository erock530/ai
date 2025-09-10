import openai
from dotenv import load_dotenv
import os
import pandas as pd
import requests
from agent_logic.agent import ResponseConstructor

load_dotenv()  # take environment variables from .env.

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

responder = ResponseConstructor()

def post_message(role, message, response_url, headers, data, message_ts):
    thread_message = {'role': role, 'content': message}
    timestamp = pd.Timestamp.now()
    thread_response_data = data.copy()
    thread_response_data['text'] = f'*{role}:*\n{message}\n\n'
    thread_response_data['thread_ts'] = message_ts
    _ = requests.post(url=response_url, headers=headers, data=thread_response_data)
    return thread_message, timestamp

def post_process(response):
    # replace '**' with single '*' for bold formatting
    response = response.replace('**', '*')
    return response

def qa(messages, response_url, headers, data, message_ts):
    def post_thread(role, response, thread_messages, timestamps):
        thread_message, timestamp = post_message(role, response, response_url, headers, data, message_ts)
        thread_messages.append(thread_message)
        timestamps.append(timestamp)

    response, agent_messages, timestamps = responder(messages[-20:], post_thread)
    response = post_process(response)
    return agent_messages, timestamps, response

if __name__ == '__main__':
    # print(qa("What is the capital of France?"))
    pass