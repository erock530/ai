# Running docker

use `docker-compose up --build` to run the app

use `docker-compose down -v` to remove volumes and re-run to re-populate database

## testing

```bash
curl -H "Authorization: fY7****************w6c" http://localhost:5000/populate_database

curl -X POST http://localhost:5000/add_message -H "Authorization: fY7****************w6c" -H "Content-Type: application/json" -d "{\"user_id\": \"user123\", \"message_content\": \"This is a new message from user123!\", \"timestamp\": \"2024-07-29T12:30:00\", \"is_user_message\": true}"

curl -X POST http://localhost:5000/add_agent_conversation -H "Authorization: fY7****************w6c" -H "Content-Type: application/json" -d "{\"message_id\": 4, \"agent_name\": \"Agent007\", \"message_content\": \"Reply from Agent007.\", \"timestamp\": \"2024-07-29T12:31:00\"}"

curl -H "Authorization: fY7****************w6c" http://localhost:5000/messages

curl -H "Authorization: fY7****************w6c" http://localhost:5000/messages/user123

curl -H "Authorization: fY7****************w6c" http://localhost:5000/agent_conversations

curl -H "Authorization: fY7****************w6c" http://localhost:5000/agent_conversations/user123

curl -H "Authorization: fY7****************w6c" http://localhost:5000/users

curl -H "Authorization: fY7****************w6c" -X DELETE http://localhost:5000/delete_user/user123
```
