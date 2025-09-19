from app import create_app
import os

app = create_app()

# Print DATABASE_URL to check which DB is being used
print("DATABASE_URL being used:", os.getenv("DATABASE_URL"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
