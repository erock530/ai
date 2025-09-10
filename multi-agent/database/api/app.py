from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv
import logging
import os
from functools import wraps
from psycopg2 import IntegrityError

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Environment variables
app.config['DB_API_KEY'] = os.getenv('DB_API_KEY')
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("POSTGRES_DB")   # Updated to match .env naming
DB_USER = os.getenv("POSTGRES_USER") # Updated to match .env naming
DB_PASS = os.getenv("POSTGRES_PASSWORD") # Updated to match .env naming

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Authorization') == app.config['DB_API_KEY']:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 403
    return decorated_function

# Connect to the PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS)
    return conn

@app.route('/add_message', methods=['POST'])
@require_api_key
def add_message():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    # Ensure your request includes 'is_user_message' which is a boolean
    cur.execute("""
        INSERT INTO MainMessages (user_id, message_content, timestamp, is_user_message)
        VALUES (%s, %s, %s, %s) RETURNING message_id;
    """, (data['user_id'], data['message_content'], data['timestamp'], data['is_user_message']))
    message_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message_id': message_id}), 201

# Query messages
@app.route('/messages', methods=['GET'])
@require_api_key
def get_messages():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM MainMessages;")
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(messages), 200

@app.route('/agent_conversations', methods=['GET'])
@require_api_key
def get_agent_conversations():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM AgentConversations;")
    conversations = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(conversations), 200

@app.route('/messages/<user_id>', methods=['GET'])
@require_api_key
def get_messages_for_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM MainMessages WHERE user_id = %s;", (user_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(messages), 200

@app.route('/agent_conversations/<user_id>', methods=['GET'])
@require_api_key
def get_agent_conversations_for_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ac.* FROM AgentConversations ac
        JOIN MainMessages mm ON ac.message_id = mm.message_id
        WHERE mm.user_id = %s;
    """, (user_id,))
    conversations = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(conversations), 200

@app.route('/users', methods=['GET'])
@require_api_key
def list_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM MainMessages;")
    user_ids = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([user_id[0] for user_id in user_ids]), 200

@app.route('/add_agent_conversation', methods=['POST'])
@require_api_key
def add_agent_conversation():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO AgentConversations (message_id, agent_name, message_content, timestamp)
            VALUES (%s, %s, %s, %s) RETURNING thread_message_id;
        """, (data['message_id'], data['agent_name'], data['message_content'], data['timestamp']))
        thread_message_id = cur.fetchone()[0]
        conn.commit()
        return jsonify({'thread_message_id': thread_message_id}), 201
    except IntegrityError as e:
        conn.rollback()  # important to rollback the transaction, reset the state
        return jsonify({'error': 'Invalid message_id or other integrity error', 'details': str(e)}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Failed to add agent conversation', 'details': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/populate_database', methods=['GET'])
@require_api_key
def populate_database():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Sample data for MainMessages
        messages = [
            ('user1', 'Hello from user1!', '2024-07-29 12:00:00', True),
            ('user2', 'Hello from user2!', '2024-07-29 12:05:00', True),
            ('user3', 'Hello from user3!', '2024-07-29 12:10:00', False),
        ]
        cur.executemany("""
            INSERT INTO MainMessages (user_id, message_content, timestamp, is_user_message)
            VALUES (%s, %s, %s, %s);
        """, messages)

        # Assuming some messages already exist and have IDs 1, 2, 3
        conversations = [
            (1, 'Agent A', 'Response from Agent A to user1', '2024-07-29 12:01:00'),
            (2, 'Agent B', 'Response from Agent B to user2', '2024-07-29 12:06:00'),
            (3, 'Agent C', 'Response from Agent C to user3', '2024-07-29 12:11:00'),
        ]
        cur.executemany("""
            INSERT INTO AgentConversations (message_id, agent_name, message_content, timestamp)
            VALUES (%s, %s, %s, %s);
        """, conversations)

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Database populated successfully'}), 200
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/delete_user/<user_id>', methods=['DELETE'])
@require_api_key
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # First, delete related entries from AgentConversations
        # This assumes you know the relationship or can infer it from MainMessages
        cur.execute("""
            DELETE FROM AgentConversations
            WHERE message_id IN (
                SELECT message_id FROM MainMessages WHERE user_id = %s
            );
        """, (user_id,))

        # Then, delete entries from MainMessages
        cur.execute("DELETE FROM MainMessages WHERE user_id = %s;", (user_id,))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'message': f'All data for user {user_id} deleted successfully'}), 200

    except Exception as e:
        conn.rollback()  # Rollback transaction on error
        cur.close()
        conn.close()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
    # Uncomment to test population on startup
    # populate_database()