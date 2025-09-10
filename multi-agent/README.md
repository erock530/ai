# Personal-Multi-Agent-System (PMAS)

## Overview

**Personal-Multi-Agent-System (PMAS)** is a gamified multi-agent platform where each AI agent serves as a specialized advisor, ranging from physicians to personal trainers. Designed to provide personalized, daily guidance, PMAS helps users navigate life’s challenges with insights from diverse perspectives.

## Features

- **Multi-Agent Interaction**: Engage with various AI-driven agents each specialized in different fields.
- **Daily Insights**: Receive daily advice and guidance tailored to personal needs and situations.
- **Gamified Experience**: Enjoy a user-friendly, gamified interface that makes interaction intuitive and engaging.
- **Diverse Perspectives**: Access a broad spectrum of viewpoints to make well-rounded decisions.

## Getting Started

To get started with PMAS, clone the repository and follow the installation instructions below:

```bash
git clone https://github.com/yourusername/personal-multi-agent-system.git
cd personal-multi-agent-system
# follow setup instructions
```

### Tuneling

Install Ngrok for server tuneling. It connects server running locally on your machine with the internet and serves as the backend to slack api calls. Before running it, you will have to create free account on https://ngrok.com/. There you will have to get authentication token and pass it to termianl. To do this, navigate to directory where you have ngrok.exe and execute `ngrok authtoken YOUR_AUTHTOKEN`. Now you are ready to run tuneling `ngrok http 3000`.

### Important links

`https://api.slack.com/apps/A07CCA5A33M/event-subscriptions` - changing backend url
`https://microsoft.github.io/autogen/docs/notebooks/agentchat_society_of_mind/` - current agent implementation

`https://orion-backend.azurewebsites.net/slack/events` - backend server url

### Docker deployment

To run docker locally - navigate to repo location, then execute in terminal:

`docker build -t slack-flask-app .`

`docker run -p 3000:3000 slack-flask-app`

For deployment to dockerhub:

`docker login`

`docker tag slack-flask-app antonidabrowski/slack-flask-app:latest`

`docker push antonidabrowski/slack-flask-app:latest`

### Agents

v0: GPT-4mini + system prompt

v1: 1-1-1 response : judge : correction (based on GPT-4mini)

v2: AutoGen - multiagent


## Contributors

Antoni Czapski
