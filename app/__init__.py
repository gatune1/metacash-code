import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# ---------------- Extensions ----------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ---------------- Config ----------------
    # Use live Postgres if DATABASE_URL exists, else fallback to local SQLite
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["DEBUG"] = False
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///metacash.db"
        app.config["DEBUG"] = True

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # ---------------- Initialize Extensions ----------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # ---------------- Import Models & Blueprints ----------------
    from app.models import User
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp

    # ---------------- Flask-Login ----------------
    login_manager.login_view = "user.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------- Register Blueprints ----------------
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ---------------- Optional: Debug - list all routes ----------------
    @app.route("/routes")
    def list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = f"{rule.endpoint:30s} {methods:20s} {rule}"
            output.append(line)
        return "<pre>" + "\n".join(sorted(output)) + "</pre>"

    return app
