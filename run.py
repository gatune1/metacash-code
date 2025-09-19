import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Print at runtime to ensure environment variables are loaded
    print("DATABASE_URL at runtime:", os.getenv("DATABASE_URL"))
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000)),
        debug=False  # turn off debug in production
    )
