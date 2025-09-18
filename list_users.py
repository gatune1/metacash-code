from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    users = User.query.all()
    if not users:
        print("ℹ️ No users found.")
    else:
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Admin: {u.is_admin}")
