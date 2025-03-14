FROM python:3.9-slim

WORKDIR /app

COPY server.py /app/
COPY models.py /app/
COPY static /app/static
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=server.py

EXPOSE 8080

CMD ["python", "server.py"]
