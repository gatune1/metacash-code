import os

class Config:
    # Default database: use DATABASE_URL (Postgres) if set, else SQLite for local dev
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///metacash.db"  # local fallback
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Point directly to live Postgres DB on Render
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "postgresql://metacash_user:lt4HPKba6kEuk8RdaXDLFKY906jXUxue@dpg-d36ca3jipnbc7392488g-a/metacash"
    )
