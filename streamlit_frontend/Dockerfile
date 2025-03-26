# Use the official Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the entire streamlit_frontend folder to /app
COPY streamlit_frontend /app/streamlit_frontend

# Copy the requirements file and install dependencies
COPY streamlit_frontend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose Streamlit's default port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "/app/streamlit_frontend/streamlit_app.py", "--server.port=8501"]
