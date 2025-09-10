# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the database_mvp directory into the container
COPY ./database_mvp ./database_mvp

# Copy the agent_logic directory into the container
COPY ./agent_logic ./agent_logic

# Set environment variable to prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Expose the port that the app runs on
EXPOSE 3000

# Run the application
CMD ["python", "app.py"]