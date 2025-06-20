from app import app, db, init_db

with app.app_context():
    db.create_all()  # Create database tables
    init_db()        # Add initial data
    print("Database initialized and dummy data added.")
