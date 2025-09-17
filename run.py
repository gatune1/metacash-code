from app import create_app, db
from app.models import User, Payment

app = create_app()

with app.app_context():
    db.create_all()  # Create tables

if __name__ == '__main__':
    app.run(debug=True)
