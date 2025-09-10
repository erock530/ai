FROM python:3.8-slim
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Gunicorn will serve the app, install it
RUN pip install gunicorn

# Copy the Flask app and the .env file
COPY . .

EXPOSE 5000

# Start Gunicorn with multiple worker processes
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "app:app"]
