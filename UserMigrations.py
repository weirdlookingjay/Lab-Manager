# migrations.py
import os
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Initialize SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(256), nullable=False) 
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)

def create_users_table():
    """Create the users table."""
    Base.metadata.create_all(engine)
    print("Users table created successfully.")

def drop_users_table():
    """Drop the users table."""
    Base.metadata.drop_all(engine)
    print("Users table dropped successfully.")

def alter_users_table():
    """Alter the users table to increase password length."""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ALTER COLUMN password TYPE VARCHAR(256)"))
        conn.commit()
    print("Users table altered successfully.")

if __name__ == "__main__":
    # Example usage
    action = input("Enter 'create' to create the users table, 'alter' to alter it, or 'drop' to drop it: ").strip().lower()
    if action == 'create':
        create_users_table()
    elif action == 'alter':
        alter_users_table()
    elif action == 'drop':
        drop_users_table()
    else:
        print("Invalid action. Please enter 'create' or 'drop'.")