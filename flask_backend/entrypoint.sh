#!/bin/bash

echo "Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started!"

# Run database migrations
flask db upgrade

# Populate database
python seed_db.py

# Start Flask application
exec python app.py
