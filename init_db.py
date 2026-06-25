from database import Base, engine
import models  # noqa: F401
import models.entities  # noqa: F401

if __name__ == "__main__":
    # Create missing tables with current schema.
    # This is non-destructive and preserves existing data.
    Base.metadata.create_all(bind=engine)
    print("Database initialized. Existing data was preserved.")
