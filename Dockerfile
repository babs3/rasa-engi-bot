FROM rasa/rasa-sdk:3.6.2

WORKDIR /app

COPY ./actions/requirements.txt /app/requirements.txt
COPY ./vector_store /app/vector_store

USER root

COPY ./actions /app/actions

RUN pip install -r /app/requirements.txt
RUN python -m spacy download en_core_web_sm
RUN python -m nltk.downloader -d /app/nltk_data wordnet omw-1.4

# Pre-download NLTK wordnet data
RUN mkdir -p /app/nltk_data && python -m nltk.downloader -d /app/nltk_data wordnet

# Ensure NLTK uses the downloaded data
ENV NLTK_DATA=/app/nltk_data

# Set environment variable for cache directory
ENV TRANSFORMERS_CACHE=/app/cache

# Create cache directory with appropriate permissions
RUN mkdir -p /app/cache && chown -R 1000:1000 /app/cache


USER 1000