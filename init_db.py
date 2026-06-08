from database import Base, engine
import models  # noqa: F401

if __name__ == "__main__":
    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)
    # Create tables with current schema
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")
