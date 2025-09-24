from app import create_app, db
from app.models import User, Payment

app = create_app()

with app.app_context():
    declined_payments = Payment.query.filter_by(status="declined").all()
    count = 0

    for payment in declined_payments:
        if payment.user and payment.user.status != "new":
            payment.user.status = "new"
            count += 1

    db.session.commit()
    print(f"✅ Reset {count} users with declined payments to 'new'")
