from flask import Flask
from flask_backend.models import *
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

@app.route("/api/course_classes/<course>", methods=["GET"])
def get_course_classes(course):
    classes = Classes.query.filter(Classes.course == course).all()
    return jsonify([{"code": c.code, "number": c.number, "course": c.course} for c in classes])

@app.route("/api/teacher_classes/<email>", methods=["GET"])
def get_teacher_classes(email):
    teacher = Teacher.query.join(Users).filter(Users.email == email).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
    print(teacher.classes)
    classes = teacher.classes.split(",")
    classes = Classes.query.filter(Classes.code.in_(classes)).all()

    teacher_classes = [{"id": c.id, "code": c.code, "number": c.number, "course": c.course} for c in classes]
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

@app.route("/api/get_student/<email>", methods=["GET"])
def get_student(email):
    student = Student.query.join(Users).filter(Users.email == email).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"user_id": student.user_id, "student_up": student.up, "course": student.course, "year": student.year, "classes": student.classes})

@app.route("/api/get_user/<email>", methods=["GET"])
def get_user(email):
    user = Users.query.filter(Users.email == email).first()
    print("User:")
    print(user)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "name": user.name, "role": user.role, "email": user.email})

@app.route("/api/message_history/<user_id>", methods=["GET"])
def get_message_history(user_id):
    history = MessageHistory.query.filter(MessageHistory.user_id == user_id).all()
    return jsonify([{"question": h.question, "response": h.response, "timestamp": h.timestamp} for h in history])

@app.route("/api/authenticate", methods=["POST"])
def authenticate():
    data = request.json
    user = Users.query.filter(Users.email == data["email"], Users.password == data["password"]).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"id": user.id, "name": user.name, "role": user.role, "email": user.email}), 200

@app.route("/api/save_message_history/<user_id>", methods=["POST"])
def save_message_history(user_id):
    data = request.json
    history = MessageHistory(user_id=user_id, question=data["question"], response=data["response"])
    db.session.add(history)
    db.session.commit()
    return jsonify({"message": "History saved"})

@app.route("/api/register_student", methods=["POST"])
def register_student():
    data = request.json
    user = Users(name=data["name"], role="Student", email=data["email"], password=data["password"])
    db.session.add(user)
    db.session.commit()

    classes = ",".join(data["classes"].split(","))
    student = Student(up=data["up"], user_id=user.id, course=data["course"], year=data["year"], classes=classes)
    db.session.add(student)
    db.session.commit()
    return jsonify({"message": "Student registered"})

@app.route("/api/register_teacher", methods=["POST"])
def register_teacher():
    data = request.json
    user = Users(name=data["name"], role="Teacher", email=data["email"], password=data["password"])
    db.session.add(user)
    db.session.commit()

    classes = data["classes"].split(",")
    teacher = Teacher(user_id=user.id, classes=classes)
    db.session.add(teacher)
    db.session.commit()
    return jsonify({"message": "Teacher registered"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
