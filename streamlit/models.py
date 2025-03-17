from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # "student" or "teacher"
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Student fields
    up_id = db.Column(db.String(20), unique=True, nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(10), nullable=True)

    # Teacher fields
    courses = db.Column(db.Text, nullable=True)  # Comma-separated values

    def __init__(self, role, email, password, up_id=None, course=None, year=None, courses=None):
        self.role = role
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.up_id = up_id
        self.course = course
        self.year = year
        self.courses = ",".join(courses) if courses else None  # Convert list to comma-separated string if needed


class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, user_message, bot_response):
        self.user_id = user_id
        self.user_message = user_message
        self.bot_response = bot_response
