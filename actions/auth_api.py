from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from .config import Config, db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    up_id = db.Column(db.String(20), unique=True, nullable=True)  # For students
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(10), nullable=True)

    def __init__(self, name, role, email, password, up_id=None, course=None, year=None):
        self.name = name
        self.role = role
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.up_id = up_id
        self.course = course
        self.year = year

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "User already exists"}), 400
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and bcrypt.check_password_hash(user.password, data["password"]):
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)

