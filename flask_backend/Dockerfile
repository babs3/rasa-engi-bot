FROM python:3.9-slim

WORKDIR /app

COPY ./flask_backend/app.py /app/app.py
COPY ./flask_backend/requirements.txt /app/requirements.txt
COPY ./shared_models /app/shared_models

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["python", "app.py"]