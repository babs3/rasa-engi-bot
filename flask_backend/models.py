from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Users Table (Parent for Student and Teacher)
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), nullable=False)  # "student" or "teacher"
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Message History Table
class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Student Table (Extends Users)
class Student(db.Model):
    up = db.Column(db.String(50), primary_key=True)  # Unique student identifier
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    classes = db.Column(db.String, nullable=False) # Comma-separated class code-number


# Teacher Table (Extends Users)
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    classes = db.Column(db.String, nullable=False) # Comma-separated class codes

# Classes Table
class Classes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)

# Student Progress Table
class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_up = db.Column(db.String(50), db.ForeignKey('student.up'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    pdfs = db.Column(db.String(255), nullable=True)  # Comma-separated PDF references
    response_time = db.Column(db.DateTime, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
