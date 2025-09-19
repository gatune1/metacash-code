import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig

# ---------------- Extensions ----------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # ---------------- Config ----------------
    if os.getenv("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

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
    app.register_blueprint(user_bp)   # no prefix
    app.register_blueprint(admin_bp)  # admin routes stay under /admin

    # ---------------- Optional: List all routes for debugging ----------------
    @app.route("/routes")
    def list_routes():
        import urllib
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = f"{rule.endpoint:30s} {methods:20s} {rule}"
            output.append(line)
        return "<pre>" + "\n".join(sorted(output)) + "</pre>"

    return app
