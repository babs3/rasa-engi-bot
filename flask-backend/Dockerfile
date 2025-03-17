FROM python:3.9-slim

WORKDIR /app

COPY app.py /app/
COPY models.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["python", "app.py"]