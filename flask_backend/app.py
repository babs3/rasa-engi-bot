from flask import Flask
from shared_models.models import *
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask import jsonify
from flask import request

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

@app.route("/api/student_progress/<student_up>", methods=["GET"])
def get_student_progress(student_up):
    progress = StudentProgress.query.filter(StudentProgress.student_up == student_up).all()
    return jsonify([{"class_id": p.class_id, "question": p.question, "response": p.response, "topic": p.topic, "pdfs": p.pdfs, "timestamp": p.timestamp} for p in progress])

@app.route("/api/save_progress/<student_up>", methods=["POST"])
def save_progress(student_up):
    data = request.json
    progress = StudentProgress(student_up=student_up, class_id=data["class_id"], question=data["question"], response=data["response"], topic=data["topic"], pdfs=data["pdfs"])
    db.session.add(progress)
    db.session.commit()
    return jsonify({"message": "Progress saved"})

@app.route("/api/get_student_up/<email>", methods=["GET"])
def get_student_up(email):
    student = Student.query.join(Users).filter(Users.email == email).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"student_up": student.up})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
