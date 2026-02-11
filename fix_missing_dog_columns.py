import sqlite3

DB_PATH = "az_marketing.db"

def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"Successfully added column '{column_name}' to table '{table_name}'.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"Column '{column_name}' already exists in table '{table_name}'.")
        else:
            print(f"Error adding column '{column_name}': {e}")

def main():
    print(f"Connecting to database: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Add dog_breed
        add_column_if_not_exists(cursor, "calls", "dog_breed", "VARCHAR(100)")
        
        # Add dog_size
        add_column_if_not_exists(cursor, "calls", "dog_size", "VARCHAR(50)")

        conn.commit()
        conn.close()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    main()
