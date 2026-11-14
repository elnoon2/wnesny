"""Idempotent seed script to populate the predefined interests catalog."""

from app import create_app
from app.extensions import db
from app.models import Interest

INITIAL_INTERESTS = [
    # Technology & Engineering
    {"name": "Artificial Intelligence", "category": "Technology"},
    {"name": "Software Development", "category": "Technology"},
    {"name": "Data Science", "category": "Technology"},
    {"name": "Cybersecurity", "category": "Technology"},
    {"name": "Robotics & Hardware", "category": "Technology"},
    {"name": "Web & Mobile Design", "category": "Technology"},

    # Entrepreneurship & Business
    {"name": "Startups & Entrepreneurship", "category": "Business"},
    {"name": "Investing & Finance", "category": "Business"},
    {"name": "Marketing & Growth", "category": "Business"},
    {"name": "Product Management", "category": "Business"},

    # Sports & Fitness
    {"name": "Football / Soccer", "category": "Sports"},
    {"name": "Basketball", "category": "Sports"},
    {"name": "Gym & Fitness", "category": "Sports"},
    {"name": "Running & Marathons", "category": "Sports"},
    {"name": "Swimming", "category": "Sports"},
    {"name": "Padel & Tennis", "category": "Sports"},

    # Arts, Culture & Media
    {"name": "Cinema & Filmmaking", "category": "Arts & Culture"},
    {"name": "Photography", "category": "Arts & Culture"},
    {"name": "Graphic Design", "category": "Arts & Culture"},
    {"name": "Reading & Literature", "category": "Arts & Culture"},
    {"name": "History & Philosophy", "category": "Arts & Culture"},

    # Music
    {"name": "Indie & Rock Music", "category": "Music"},
    {"name": "Hip-Hop & R&B", "category": "Music"},
    {"name": "Electronic & House", "category": "Music"},
    {"name": "Classical & Instrumental", "category": "Music"},
    {"name": "Arabic Classical & Folk", "category": "Music"},

    # Lifestyle & Hobbies
    {"name": "Traveling & Backpacking", "category": "Lifestyle"},
    {"name": "Coffee Culture", "category": "Lifestyle"},
    {"name": "Cooking & Gastronomy", "category": "Lifestyle"},
    {"name": "Board Games", "category": "Gaming & Hobbies"},
    {"name": "Video Games & Esports", "category": "Gaming & Hobbies"},
    {"name": "Volunteering & Community", "category": "Social"},
]


def seed_interests(app=None) -> int:
    """Insert default interests into the database without creating duplicates.

    Returns the count of newly inserted interests.
    """
    if app is None:
        app = create_app()

    inserted_count = 0
    with app.app_context():
        for item in INITIAL_INTERESTS:
            existing = Interest.query.filter_by(name=item["name"]).first()
            if not existing:
                interest = Interest(name=item["name"], category=item["category"])
                db.session.add(interest)
                inserted_count += 1
            else:
                # Keep category up to date if modified
                if existing.category != item["category"]:
                    existing.category = item["category"]

        db.session.commit()

    return inserted_count


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Ensure tables exist in case run before migrations
        db.create_all()
        count = seed_interests(app)
        total = Interest.query.count()
        print(f"Seed completed. {count} new interests inserted. Total interests in database: {total}")
