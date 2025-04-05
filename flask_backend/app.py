from flask import Flask, render_template_string
from flask_backend.models import *
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask import jsonify
from flask import request
import hashlib
from flask_mail import Mail, Message
import secrets
import random

app = Flask(__name__)

# Flask-Mail Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Use your SMTP provider
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "flash.app.noreply@gmail.com"
app.config["MAIL_PASSWORD"] = "hptf jtwh hujq pvpr"  # App-specific password
app.config["MAIL_DEFAULT_SENDER"] = "flash.app.noreply@gmail.com"

mail = Mail(app)

app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}'
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production!
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)  # For database migrations
jwt = JWTManager(app)

@app.route("/api/classes", methods=["GET"])
def get_classes():
    classes = Classes.query.all()
    return jsonify([{"id": c.id, "code": c.code, "number": c.number, "course": c.course} for c in classes])

@app.route("/api/course_classes/<course>", methods=["GET"])
def get_course_classes(course):
    classes = Classes.query.filter(Classes.course.like(f"%{course}%")).all()
    return jsonify([{"code": c.code, "number": c.number, "course": c.course} for c in classes])

@app.route("/api/teacher_classes/<email>", methods=["GET"])
def get_teacher_classes(email):
    teacher = Teacher.query.join(Users).filter(Users.email == email).first()
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404
    
    # Extract class codes (assuming they are stored as comma-separated values)
    class_codes = [code.split("-")[0] for code in teacher.classes.split(",") if code.strip()]
    # remove duplicates
    class_codes = list(set(class_codes))

    # Query Classes table for matching codes
    classes = Classes.query.filter(Classes.code.in_(class_codes)).all()

    return jsonify([{"id": c.id, "code": c.code, "number": c.number, "course": c.course} for c in classes])


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
    progress = StudentProgress(student_up=student_up, class_id=data["class_id"], question=data["question"], response=data["response"], topic=data["topic"], pdfs=data["pdfs"], response_time=data["response_time"])
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
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "name": user.name, "role": user.role, "email": user.email, "token": user.token, "is_verified": user.is_verified})

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
    return jsonify({"id": user.id, "name": user.name, "role": user.role, "email": user.email, "token": user.token, "is_verified": user.is_verified})

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
    
    # Generate confirmation token
    #confirmation_token = secrets.token_urlsafe(6)
    confirmation_token = f"{random.randint(100000, 999999)}"
    # Store user with `is_verified=False`
    user = Users(name=data["name"], role="Student", email=data["email"], password=data["password"], token=confirmation_token)
    db.session.add(user)
    db.session.commit()

    classes = ",".join(data["classes"].split(","))
    student = Student(up=data["up"], user_id=user.id, course=data["course"], year=data["year"], classes=classes)
    db.session.add(student)
    db.session.commit()
    
    return send_confirmation_email(data["email"], confirmation_token)


@app.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    print("🚀 Route hit!")  # Debug print
    
    user = Users.query.filter_by(token=token).first()
    if not user:
        print("❌ Invalid or expired token")
        return "<h2>❌ Invalid or expired token</h2>", 400

    print(f"🔹 User found: {user.email}, Verified status before: {user.is_verified}")
    
    try:
        user.is_verified = True
        db.session.commit()
        print("✅ User verification updated successfully!")

        return "<h2>✅ Email confirmed successfully! You can now log in.</h2>", 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database Error: {str(e)}")
        return f"<h2>❌ Database Error: {str(e)}</h2>", 500

@app.route("/api/update_user_verification", methods=["POST"])
def update_user_verification():
    data = request.json
    user = Users.query.filter_by(email=data["email"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if str(user.token) == data["verification_code"]:
        user.is_verified = "True"
        db.session.commit()
        return jsonify({"message": "User verified successfully"}), 200
    else:
        return jsonify({"error": "Invalid verification code"}), 400


@app.route("/api/register_teacher", methods=["POST"])
def register_teacher():
    data = request.json
    
    # Generate confirmation token
    #confirmation_token = secrets.token_urlsafe(6)
    confirmation_token = f"{random.randint(100000, 999999)}"
    # Store user with `is_verified=False`
    user = Users(name=data["name"], role="Teacher", email=data["email"], password=data["password"], token=confirmation_token)
    db.session.add(user)
    db.session.commit()

    classes = ",".join(data["classes"].split(","))

    teacher = Teacher(user_id=user.id, classes=classes)
    db.session.add(teacher)
    db.session.commit()
    
    # Send confirmation email
    return send_confirmation_email(data["email"], confirmation_token)


def send_confirmation_email(email, token):

    subject = "✅ Verify Your Email Address"
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #f4f4f4;
      color: #333;
      padding: 20px;
    }}
    .container {{
      background-color: #fff;
      padding: 20px;
      border-radius: 10px;
      max-width: 500px;
      margin: auto;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .otp {{
      font-size: 24px;
      font-weight: bold;
      background-color: #e8f0fe;
      padding: 10px;
      border-radius: 6px;
      display: inline-block;
      letter-spacing: 2px;
    }}
    .footer {{
      margin-top: 20px;
      font-size: 12px;
      color: #888;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h2>🔐 Email Verification</h2>
    <p>Hi there,</p>
    <p>Use the code below to verify your account:</p>
    <div class="otp">{token}</div>
    <p>If you didn’t request this, you can safely ignore this email.</p>
    <p>Thanks,<br><strong>Your Chatbot Team</strong></p>
    <div class="footer">
      &copy; 2025 Your Chatbot Platform. All rights reserved.
    </div>
  </div>
</body>
</html>
    """

    try:
        msg = Message(subject, recipients=[email], html=html_body)
        mail.send(msg)
        #print(f"Confirmation email sent to {email}")
        return jsonify({"message": f"✅ Confirmation email sent to {email}"}), 200
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify({"message": f"❌ Failed to send email: {e}"}), 500

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    with app.app_context():
        # Check if table is empty before seeding
        if not Classes.query.first():
            classes = [
                Classes(code="GEE", number="1", course="MEIC"),
                Classes(code="GEE", number="2", course="MEIC"),
                Classes(code="SCI", number="1", course="MEIC,MEEC"),
                Classes(code="SCI", number="2", course="MEIC,MEEC"),
                Classes(code="LGP", number="1", course="MEIC,MEEC,MM"),
            ]
            db.session.bulk_save_objects(classes)
            db.session.commit()
            print("Database seeded successfully!")
        else:
            print("Database already seeded. Skipping.")

        # Seed Default Student
        student_email = "student@example.com"
        default_student = Users.query.filter_by(email=student_email).first()
        if not default_student:
            student_user = Users(
                name="Default Student",
                role="Student",  # Ensure lowercase matches database
                email=student_email,
                password=hash_password("pass"),  # Hash password for security
                token="000000",
                is_verified="True"
            )
            db.session.add(student_user)
            db.session.commit()  # Commit to get ID

            student_entry = Student(
                up="000000000",
                user_id=student_user.id,  # Now it exists
                course="MEIC",
                year=1,
                classes="GEE-1,SCI-1,LGP-1"
            )
            db.session.add(student_entry)
            db.session.commit()
            print("Default student added!")
        else:
            print("Default student already exists. Skipping seeding.")

        # Seed Default Professor
        professor_email = "professor@example.com"
        default_professor = Users.query.filter_by(email=professor_email).first()
        if not default_professor:
            professor_user = Users(
                name="Default Professor",
                role="Teacher",  # Ensure lowercase matches database
                email=professor_email,
                password=hash_password("pass"),  # Hash password
                token="000001",
                is_verified="True"
            )
            db.session.add(professor_user)
            db.session.commit()  # Commit to get ID

            professor_entry = Teacher(
                user_id=professor_user.id,  # Now it exists
                classes="GEE-1,GEE-2,SCI-1,SCI-2,LGP-1"
            )
            db.session.add(professor_entry)
            db.session.commit()
            print("Default professor added!")
        else:
            print("Default professor already exists. Skipping seeding.")


if __name__ == "__main__":
    seed_database()
    app.run(host='0.0.0.0', port=8080)
    
