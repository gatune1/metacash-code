import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# ---------------- Extensions ----------------
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# ---------------- Config ----------------
class Config:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://metacash_user:lt4HPKba6kEuk8RdaXDLFKY906jXUxue@dpg-d36ca3jipnbc7392488g-a.oregon-postgres.render.com/metacash"
    )

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False


def create_app():
    app = Flask(__name__)

    # ---------------- Load config based on environment ----------------
    if os.getenv("FLASK_ENV") == "development":
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # ---------------- Initialize extensions ----------------
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = "user.login"

    # ---------------- Import models ----------------
    from app.models import User, Payment, Withdrawal, TriviaAnswer, Spin, WhatsAppPost

    # ---------------- Import and register blueprints ----------------
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # ---------------- User loader ----------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------- Debug route to list all routes ----------------
    @app.route("/routes")
    def list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            output.append(f"{rule} -> {rule.endpoint}")
        return "<pre>" + "\n".join(sorted(output)) + "</pre>"

    return app
