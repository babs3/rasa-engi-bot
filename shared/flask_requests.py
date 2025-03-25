import requests

def fetch_student(student_email):
    response = requests.get("http://flask-server:8080/api/get_student/" + student_email)
    return response.json() if response.status_code == 200 else {}

def fetch_student_progress(student_up, data):
    # Make the POST request to the save_progress endpoint
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

def fetch_course_classes(course):
    response = requests.get("http://flask-server:8080/api/course_classes/" + course)
    return response.json() if response.status_code == 200 else {}

def fetch_user(user_email):
    response = requests.get("http://flask-server:8080/api/get_user/" + user_email)
    return response.json() if response.status_code == 200 else {}

def fetch_message_history(user_email):
    user = fetch_user(user_email)
    if user:
        user_id = user.get("id")
        response = requests.get("http://flask-server:8080/api/message_history/" + str(user_id))
        return response.json() if response.status_code == 200 else {}
    return {}
