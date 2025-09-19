import os

class Config:
    """Base Flask configuration."""
    
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    # Use Render database if available, else fallback to local
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://metacash_user:lt4HPKba6kEuk8RdaXDLFKY906jXUxue@dpg-d36ca3jipnbc7392488g-a/metacash"
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
