import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# 1. Connect to Neon DB
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env. Please add your Neon DB connection string.")

# SQLAlchemy 2.0+ defaults to psycopg (v3). Since we have psycopg2 installed, 
# we need to ensure the dialect string uses psycopg2 explicitly.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory for interacting with the database
SessionLocal = sessionmaker(bind=engine)

# Base class for our models
Base = declarative_base()

# 2. Define the Model (Table)
class CallRecord(Base):
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, index=True)
    
    # We use BigInteger for the timestamp because milliseconds since epoch is a very large number
    ts = Column(BigInteger, index=True) 
    
    provider = Column(String, index=True)
    key_index = Column(Integer, index=True)
    model_name = Column(String)
    endpoint = Column(String)
    status = Column(String) # For example: 'ok' or 'error'
    http_status = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)

# 3. Create the table in Neon DB if it doesn't already exist
Base.metadata.create_all(bind=engine)
