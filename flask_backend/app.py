from flask import Flask
from shared_models.models import *
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask import jsonify

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}'
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)  # For database migrations
jwt = JWTManager(app)

@app.route("/api/classes", methods=["GET"])
def get_classes():
    classes = Classes.query.all()
    return jsonify([{"code": c.code, "number": c.number, "course": c.course} for c in classes])

@app.route("/api/teacher_classes/<email>", methods=["GET"])
def get_teacher_classes(email):
    teacher = Teacher.query.join(Users).filter(Users.email == email).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
    print(teacher.classes)
    classes = teacher.classes.split(",")
    classes = Classes.query.filter(Classes.code.in_(classes)).all()

    teacher_classes = [{"code": c.code, "number": c.number, "course": c.course} for c in classes]
    return jsonify({"email": email, "classes": teacher_classes})

@app.route("/api/class_progress/<class_id>", methods=["GET"])
def get_class_progress(class_id):
    progress = StudentProgress.query.filter(StudentProgress.class_id == class_id).all()
    return jsonify([{"student_up": p.student_up, "question": p.question, "response": p.response, "topic": p.topic, "pdfs": p.pdfs, "timestamp": p.timestamp} for p in progress])


if __name__ == "__main__":
    #with app.app_context():
    #   db.create_all()
    app.run(host='0.0.0.0', port=8080)
