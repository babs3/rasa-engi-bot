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
    otp = db.Column(db.Integer, nullable=True)
    is_verified = db.Column(db.String(20), default="False") # "True" or "False"
    
    # Relationship with Student (cascade delete enabled)
    student = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    teacher = db.relationship('Teacher', backref='user', uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    messages = db.relationship('MessageHistory', backref='user', cascade="all, delete-orphan", passive_deletes=True) 
    

# Student Table (Extends Users)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    up = db.Column(db.Integer, nullable=False)  # Unique student identifier
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    class_ = db.Column(db.String, nullable=False) # Comma-separated class code-number
    
    progress = db.relationship('StudentProgress', backref='user', uselist=False, cascade="all, delete-orphan", passive_deletes=True)  
    

# Teacher Table (Extends Users)
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    classes = db.Column(db.String, nullable=False) # Comma-separated class codes

# Classes Table
class Classes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)

# Message History Table
class MessageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())  
    
# Student Progress Table
class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete="CASCADE"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    pdfs = db.Column(db.String(255), nullable=True)  # Comma-separated PDF references
    response_time = db.Column(db.String(100), nullable=False)  # Time taken to generate the response in seconds
    timestamp = db.Column(db.DateTime, default=datetime.now())
