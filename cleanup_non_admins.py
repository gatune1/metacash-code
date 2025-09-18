# cleanup_non_admins.py

from app import create_app
from app.models import db, User, Payment, Withdrawal, Spin, TriviaAnswer

def delete_non_admin_users():
    app = create_app()
    with app.app_context():
        non_admins = User.query.filter_by(is_admin=False).all()

        if not non_admins:
            print("ℹ️ No non-admin users found.")
            return

        for user in non_admins:
            print(f"Deleting user: {user.username} ({user.email})")

            # Delete related records first
            Payment.query.filter_by(user_id=user.id).delete()
            Withdrawal.query.filter_by(user_id=user.id).delete()
            Spin.query.filter_by(user_id=user.id).delete()
            TriviaAnswer.query.filter_by(user_id=user.id).delete()

            # Delete the user
            db.session.delete(user)

        db.session.commit()
        print("✅ All non-admin users and their records have been deleted.")

if __name__ == "__main__":
    delete_non_admin_users()
