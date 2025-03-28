from flask import Flask
from models import db, Classes

app = Flask(__name__)
app.config.from_object("config")
db.init_app(app)

def seed_database():
    with app.app_context():
        # Check if table is empty before seeding
        if not Classes.query.first():
            classes = [
                Classes(code="CS101", number="1", course="Computer Science"),
                Classes(code="EE102", number="1", course="Electrical Engineering"),
            ]
            db.session.bulk_save_objects(classes)
            db.session.commit()
            print("Database seeded successfully!")
        else:
            print("Database already seeded. Skipping.")

if __name__ == "__main__":
    seed_database()
