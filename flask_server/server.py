from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token
import os
from models import db, bcrypt, User, UserHistory
from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
import requests

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}'
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)
bcrypt.init_app(app)
jwt = JWTManager(app)

# Rasa Server URL
RASA_URL = "http://rasa:5005/webhooks/rest/webhook"

# Serve index.html
@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

@app.route('/get_user_id', methods=['POST'])
@jwt_required()
def get_user_id():
    user_id = get_jwt_identity()
    return jsonify({"user_id": user_id})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    user_id = data.get("user_id")

    # Send user message to Rasa
    response = requests.post(
        RASA_URL,
        json={"sender": user_id, "message": user_message}
    )
    bot_messages = response.json()

    # Collect bot response
    bot_response = "\n".join([msg.get("text", "") for msg in bot_messages])

    # Log interaction in PostgreSQL
    user_id = get_jwt_identity()
    data = request.json
    user_message = data.get("user_message")
    bot_response = data.get("bot_response")
    
    if user_message and bot_response:
        interaction = UserHistory(user_id=user_id, user_message=user_message, bot_response=bot_response)
        db.session.add(interaction)
        db.session.commit()
        return jsonify({"message": "Interaction saved successfully!"}), 200
    return jsonify({"error": "Invalid data"}), 400

@app.route("/save_interaction", methods=["POST"])
@jwt_required()
def save_interaction():
    user_id = get_jwt_identity()
    print(f"  user_id: {user_id}")
    data = request.json
    user_message = data.get("user_message")
    bot_response = data.get("bot_response")
    
    if user_message and bot_response:
        interaction = UserHistory(user_id=2, user_message=user_message, bot_response=bot_response)
        db.session.add(interaction)
        db.session.commit()
        return jsonify({"message": "Interaction saved successfully!"}), 200
    return jsonify({"error": "Invalid data"}), 400

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
