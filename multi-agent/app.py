from flask import Flask, request, jsonify
import requests
import os
import agent
import logging
from database_mvp.gdrive_api import backup_db, load_db, get_user_messages, save_main_message, save_agent_conversation

app = Flask(__name__)
SLACK_TOKEN = os.getenv("SLACK_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# load the database
load_db()

# A set to keep track of processed event_ids to ensure idempotency
processed_events = set()

@app.route('/slack/events', methods=['POST'])
def slack_events():
    json_data = request.json
    # {'token': 'L8OdB2FRICZjbirG1w62ReDH', 'team_id': 'T074CJYG1EJ', 'context_team_id': 'T074CJYG1EJ', 'context_enterprise_id': None, 'api_app_id': 'A07CCA5A33M',
    #  'event': {'user': 'U074K84941G', 'type': 'message', 'ts': '1722719817.451929', 'client_msg_id': 'b6fe0e03-202c-40a4-8ec3-b323e3844628',
    #      'text': 'O czym przed chwilą rozmawialiśmy?', 'team': 'T074CJYG1EJ', 
    #      'blocks': [{'type': 'rich_text', 'block_id': 'gGIyc', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'O czym przed chwilą rozmawialiśmy?'}]}]}],
    #      'channel': 'D07BXSTLP1V', 'event_ts': '1722719817.451929', 'channel_type': 'im'},
    # 'type': 'event_callback', 'event_id': 'Ev07FG1K9QUC', 'event_time': 1722719817,
    # 'authorizations': [{'enterprise_id': None, 'team_id': 'T074CJYG1EJ', 'user_id': 'U07CR3Z26E5', 'is_bot': True, 'is_enterprise_install': False}],
    # 'is_ext_shared_channel': False,
    # 'event_context': '4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUMDc0Q0pZRzFFSiIsImFpZCI6IkEwN0NDQTVBMzNNIiwiY2lkIjoiRDA3QlhTVExQMVYifQ'}
    logging.info(f"Received event: {json_data}")
    
    if 'challenge' in json_data:
        return jsonify({'challenge': json_data['challenge']})
    
    if 'event' in json_data:
        event = json_data['event']
        event_id = json_data.get('event_id')
        
        # Check if this event_id has been processed
        if event_id in processed_events:
            logging.info(f"Duplicate event_id {event_id} detected, ignoring.")
            return jsonify({'status': 'duplicate event'}), 200
        
        # Add the event_id to the set of processed events
        processed_events.add(event_id)
        
        if event.get('type') == 'message' and not event.get('bot_id'):
            user_message = event['text']
            channel_id = event['channel']
            user_id = event['user']
            message_ts = event['ts']
            messages = get_user_messages(user_id=user_id) + [{'role': 'user', 'content': user_message}]

            # Respond with a new message
            response_url = 'https://slack.com/api/chat.postMessage'
            headers = {'Authorization': 'Bearer ' + SLACK_TOKEN}
            data = {
                'channel': channel_id,
            }
            agent_messages, timestamps, response_message = agent.qa(messages, response_url, headers, data, message_ts)  # Get the response from the QA function
            data['text'] = response_message
            _ = requests.post(url=response_url, headers=headers, data=data)
            logging.info(f"Sent response: {response_message}")
            # save user message
            message_id = save_main_message(user_id=user_id, message_content=user_message, is_user_message=True)
            # save agent response
            _ = save_main_message(user_id=user_id, message_content=response_message, is_user_message=False)
            # save agent conversation
            save_agent_conversation(message_id=message_id, messages=agent_messages, timestamps=timestamps)
            # backup the database
            backup_db()            
    
    return jsonify({'status': 'ok'})
# U074K84941G / U07EBJYBG4T
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
