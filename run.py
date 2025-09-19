from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # ✅ Print safely for debugging (optional)
    print("DATABASE_URL being used:", app.config['SQLALCHEMY_DATABASE_URI'])

    # ✅ Use environment variables for host and port
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))

    # ✅ Turn debug off in production
    debug = os.getenv("FLASK_ENV") == "development"

    app.run(host=host, port=port, debug=debug)
