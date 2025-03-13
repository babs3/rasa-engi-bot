import os
from flask_sqlalchemy import SQLAlchemy

# Choose between SQLite and PostgreSQL
DB_TYPE = os.getenv("DB_TYPE", "postgres")  # "sqlite" or "postgres"

if DB_TYPE == "sqlite":
    DB_PATH = "sqlite:///db/app.db"
elif DB_TYPE == "postgres":
    DB_PATH = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@db/{os.getenv('POSTGRES_DB')}"

class Config:
    SQLALCHEMY_DATABASE_URI = DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()
