import sqlite3

def dump_database_records(db_path):
    """
    Dumps all records from all tables in the given SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # Get a list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print(f"No tables found in database: {db_path}")
            return

        # Iterate through each table and fetch its records
        for table_name_tuple in tables:
            table_name = table_name_tuple[0]  # Extract table name from tuple
            print(f"\n--- Table: {table_name} ---")

            # Fetch all records from the current table
            cursor.execute(f"SELECT * FROM {table_name};")
            records = cursor.fetchall()

            if not records:
                print("No records found in this table.")
                continue

            # Get the column names for printing headers
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            column_names = [column_info[1] for column_info in columns_info]  # Get column names

            # Print the column headers
            print(f"{' | '.join(column_names)}")
            print("-" * (sum(len(name) + 3 for name in column_names) - 1)) #create separator

            # Print each record in the table
            for record in records:
                # Format each record as a string with proper spacing
                record_str = " | ".join(map(str, record))
                print(record_str)

    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    # Specify the path to your SQLite database file
    database_path = "lambda/employee_database.db"  # Replace with the actual path

    # Check if the database file exists
    import os
    if not os.path.exists(database_path):
        print(f"Error: Database file not found at {database_path}")
    else:
        dump_database_records(database_path)
