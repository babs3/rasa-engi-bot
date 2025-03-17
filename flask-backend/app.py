from flask import Flask
from models import db  # Assuming models.py is in the same folder
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}'
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)  # For database migrations
jwt = JWTManager(app)

if __name__ == "__main__":
    #with app.app_context():
    #   db.create_all()
    app.run(host='0.0.0.0', port=8080)
