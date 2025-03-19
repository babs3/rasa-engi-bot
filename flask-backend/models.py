from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Users(db.Model):
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
        self.password = password # password is hashed in the streamlit app
        self.up_id = up_id
        self.course = course
        self.year = year
        self.courses = ",".join(courses) if courses else None  # Convert list to comma-separated string if needed


class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, user_message, bot_response):
        self.user_id = user_id
        self.user_message = user_message
        self.bot_response = bot_response

class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, student_id, user_message, bot_response):
        self.student_id = student_id
        self.user_message = user_message
        self.bot_response = bot_response
