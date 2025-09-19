from app import create_app
import os

# Create the Flask app using the factory function
app = create_app()

if __name__ == "__main__":
    # Determine host, port, and debug mode from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") != "production"  # True for dev, False for prod

    # Run the app locally (development server)
    app.run(host=host, port=port, debug=debug)
