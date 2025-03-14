from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
import os
from models import db, bcrypt, User

app = Flask(__name__, static_folder="static", static_url_path="/")

app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}'
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
bcrypt.init_app(app)
jwt = JWTManager(app)

# Serve index.html
@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "User already exists"}), 400

    new_user = User(
        role=data["role"],
        email=data["email"],
        password=data["password"], # password é hashed no model
        up_id=data.get("up_id"),
        course=data.get("course"),
        year=data.get("year"),
        courses=",".join(data.get("courses", [])) if data["role"] == "teacher" else None
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if user and bcrypt.check_password_hash(user.password, data["password"]):
        access_token = create_access_token(identity=user.id)
        return jsonify({"token": access_token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)
