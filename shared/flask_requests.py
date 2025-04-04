import requests

def fetch_student(student_email):
    response = requests.get("http://flask-server:8080/api/get_student/" + student_email)
    return response.json() if response.status_code == 200 else {}

def fetch_student_progress(student_email):
    student = fetch_student(student_email)
    if not student:
        return {}
    student_up = student.get("student_up")
    response = requests.get("http://flask-server:8080/api/student_progress/" + student_up)
    return response.json() if response.status_code == 200 else {}

def save_progress(student_up, data):
    response = requests.post("http://flask-server:8080/api/save_progress/" + student_up, json=data)
    return response.json() if response.status_code == 200 else {}

def fetch_classes():
    response = requests.get("http://flask-server:8080/api/classes")
    return response.json() if response.status_code == 200 else {}

def fetch_class_progress(class_id):
    response = requests.get("http://flask-server:8080/api/class_progress/" + str(class_id))
    return response.json() if response.status_code == 200 else {}

def fetch_teacher_classes(teacher_email):
    response = requests.get("http://flask-server:8080/api/teacher_classes/" + teacher_email)
    return response.json() if response.status_code == 200 else {}

#def fetch_course_classes(course):
#    response = requests.get("http://flask-server:8080/api/course_classes/" + course)
#    return response.json() if response.status_code == 200 else {}

def fetch_user(user_email):
    response = requests.get("http://flask-server:8080/api/get_user/" + user_email)
    return response.json() if response.status_code == 200 else {}

def fetch_message_history(user_email):
    user = fetch_user(user_email)
    if not user:
        return {}
    user_id = user.get("id")
    response = requests.get("http://flask-server:8080/api/message_history/" + str(user_id))
    return response.json() if response.status_code == 200 else {}

def save_message_history(user_email, data):
    user = fetch_user(user_email)
    if not user:
        return {}
    user_id = user.get("id")
    response = requests.post("http://flask-server:8080/api/save_message_history/" + str(user_id), json=data)
    return response.json() if response.status_code == 200 else {}

def authenticate_user(email, password):
    response = requests.post("http://flask-server:8080/api/authenticate", json={"email": email, "password": password})
    return response.json() if response.status_code == 200 else {}

def register_student(name, email, password, up, course, year, classes):
    response = requests.post("http://flask-server:8080/api/register_student", json={"name": name, "email": email, "password": password, "up": up, "course": course, "year": year, "classes": classes})
    return response.json() if response.status_code == 200 else {}

def register_teacher(name, email, password, classes):
    response = requests.post("http://flask-server:8080/api/register_teacher", json={"name": name, "email": email, "password": password, "classes": classes})
    return response.json() if response.status_code == 200 else {}

def update_user_verification(email, verification_code):
    response = requests.post("http://flask-server:8080/api/update_user_verification", json={"email": email, "verification_code": verification_code})
    return response.json() if response.status_code == 200 else {}