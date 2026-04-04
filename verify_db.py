import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("POSTGRES_DATABASE_URL")
engine = create_engine(db_url)

try:
    with engine.connect() as connection:
        print("✓ Connected to database successfully")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found: {tables}")
        
        expected_tables = ["conversations", "messages"]
        all_present = all(t in tables for t in expected_tables)
        
        if all_present:
            print("✓ All expected tables are present")
        else:
            missing = [t for t in expected_tables if t not in tables]
            print(f"✗ Missing tables: {missing}")
except Exception as e:
    print(f"✗ Failed to connect: {e}")
