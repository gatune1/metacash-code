import os

class Config:
    # Default to SQLite for local dev
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///metacash.db"
    )

    # Avoid SQLAlchemy warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key (use environment variable in production)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
