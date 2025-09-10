CREATE TABLE MainMessages (
    message_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    is_user_message BOOLEAN NOT NULL DEFAULT TRUE  -- Ensure this line is correctly defined
);


CREATE TABLE AgentConversations (
    thread_message_id SERIAL PRIMARY KEY,
    message_id INT NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (message_id) REFERENCES MainMessages(message_id)
);
