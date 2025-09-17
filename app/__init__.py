from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metacash.db'
    app.config['SECRET_KEY'] = 'your-secret-key'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import models and blueprints
    from app.models import User
    from app.routes.user_routes import user_bp
    from app.routes.admin_routes import admin_bp

    # Flask-Login setup
    login_manager.login_view = 'user.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(user_bp)        # user routes
    app.register_blueprint(admin_bp)       # admin routes already have /admin prefix

    return app
