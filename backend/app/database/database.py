
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# Load the .env file
load_dotenv()

# Fetch values
database_url = os.getenv("DATABASE_URL")



engine = create_async_engine(database_url, echo=True,pool_recycle=120,pool_pre_ping=True,pool_size=30 )

# Create a session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    
)

# Base class for declarative models
Base = declarative_base()

# Dependency to get the database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

