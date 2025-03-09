FROM rasa/rasa-sdk:3.6.2

WORKDIR /app

COPY ./actions/requirements.txt /app/requirements.txt
#COPY ./.env /app/.env

USER root

COPY ./actions /app/actions

RUN pip install -r /app/requirements.txt

USER 1000