FROM python:3.9-slim

WORKDIR /app

# Copy the entire flask_backend folder to /app
COPY flask_backend /app/flask_backend

# Copy the requirements file and install dependencies
COPY flask_backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set PYTHONPATH to include /app
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "/app/flask_backend/app.py"]