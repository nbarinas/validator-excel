from sqlalchemy import create_engine, inspect
from backend.database import SQLALCHEMY_DATABASE_URL

def inspect_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    columns = inspector.get_columns('calls')
    print("Columns in 'calls' table:")
    for col in columns:
        print(f"- {col['name']}")

if __name__ == "__main__":
    inspect_schema()
