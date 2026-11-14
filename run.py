import os
from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserProfile,
    Interest,
    user_interests,
    Ride,
    RideRequest,
    Conversation,
    Message,
    Review,
    Notification,
)

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)


@app.shell_context_processor
def make_shell_context():
    """Provides models and db in the flask shell context."""
    return {
        "db": db,
        "User": User,
        "UserProfile": UserProfile,
        "Interest": Interest,
        "user_interests": user_interests,
        "Ride": Ride,
        "RideRequest": RideRequest,
        "Conversation": Conversation,
        "Message": Message,
        "Review": Review,
        "Notification": Notification,
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
