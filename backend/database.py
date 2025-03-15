import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "energy_management")

# URL encode the password
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# Construct the DATABASE_URL
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for SQLAlchemy models
Base = declarative_base()
# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()