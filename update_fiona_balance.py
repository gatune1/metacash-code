from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Find user by email only
    user = User.query.filter_by(email='highgangsterz@gmail.com').first()

    if user:
        print(f"Found user: {user.email}, active: {user.is_active}")
        user.trivia_balance = 50
        user.youtube_earnings = 250
        db.session.commit()
        print(f"{user.email}'s balances updated successfully!")
    else:
        print("User not found.")
