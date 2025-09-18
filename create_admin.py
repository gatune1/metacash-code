from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Initialize app context
app = create_app()
app.app_context().push()

# ---- Admin details ----
admin_username = "Zadmin"
admin_full_name = "MetaCash Admin"
admin_email = "gatunezack01@gmail.com"
admin_mpesa_no = "0712345678"  # Update if different
admin_password = "Zack2004!"
# -----------------------

# Check if admin already exists
existing_admin = User.query.filter_by(username=admin_username).first()
if existing_admin:
    print(f"Admin '{admin_username}' already exists!")
else:
    # Create admin user
    admin_user = User(
        username=admin_username,
        full_name=admin_full_name,
        email=admin_email,
        mpesa_no=admin_mpesa_no,
        password=generate_password_hash(admin_password),
        status="active",
        is_admin=True
    )
    db.session.add(admin_user)
    db.session.commit()
    print(f"Admin '{admin_username}' created successfully!")
