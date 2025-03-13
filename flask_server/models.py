from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # "student" or "teacher"
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Student fields
    #up_id = db.Column(db.String(20), unique=True, nullable=True)
    #course = db.Column(db.String(100), nullable=True)
    #year = db.Column(db.String(10), nullable=True)

    # Teacher fields
    #courses = db.Column(db.Text, nullable=True)  # Comma-separated values
