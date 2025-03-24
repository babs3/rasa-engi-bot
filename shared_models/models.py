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

    # Relationships
    #message_history = db.relationship('MessageHistory', backref='user', lazy=True)
    #student = db.relationship('Student', uselist=False, backref='user')  # One-to-One
    #teacher = db.relationship('Teacher', uselist=False, backref='user')  # One-to-One

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

    # Relationships
    #progress = db.relationship('StudentProgress', backref='student', lazy=True)

# Teacher Table (Extends Users)
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    classes = db.Column(db.String, nullable=False) # Comma-separated class codes

    # Many-to-Many Relationship with Classes
    #classes = db.relationship('Classes', secondary='teacher_classes', back_populates='teachers')

# Classes Table
class Classes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    course = db.Column(db.String(100), nullable=False)

    # Relationships
    #students = db.relationship('Student', secondary='student_classes', back_populates='classes')
    #teachers = db.relationship('Teacher', secondary='teacher_classes', back_populates='classes')

# Student Progress Table
class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_up = db.Column(db.String(50), db.ForeignKey('student.up'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    pdfs = db.Column(db.String(255), nullable=True)  # Comma-separated PDF references
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Association Table for Student-Classes Many-to-Many
#student_classes = db.Table(
#    'student_classes',
#    db.Column('student_up', db.String(50), db.ForeignKey('student.up'), primary_key=True),
#    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'), primary_key=True)
#)

# Association Table for Teacher-Classes Many-to-Many
#teacher_classes = db.Table(
#    'teacher_classes',
#    db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.id'), primary_key=True),
#    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'), primary_key=True)
#)
