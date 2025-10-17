# migrate_data.py
import os
from sqlalchemy import create_engine, text, table, column

def migrate():
    """
    Connects to two databases and directly transfers data from source to destination.
    This script assumes the destination database schema has already been created.
    """
    # IMPORTANT: Set these environment variables in your terminal before running!
    SOURCE_DB_URL = os.getenv("SOURCE_DB_URL") # Your OLD Render DB URI
    DEST_DB_URL = os.getenv("DEST_DB_URL")   # Your NEW Neon DB URI

    if not SOURCE_DB_URL or not DEST_DB_URL:
        print("🔴 ERROR: Please set both SOURCE_DB_URL and DEST_DB_URL environment variables.")
        return

    print("Connecting to databases...")
    source_engine = create_engine(SOURCE_DB_URL)
    dest_engine = create_engine(DEST_DB_URL)
    
    # The order is critical to respect foreign key constraints!
    # Parent tables (teams, players) must come before child tables (matches, etc.).
    table_names = [
        "teams",
        "players",
        "matches",
        "match_lineups",
        "match_subs",
        "team_formation",
        "match_events"
    ]

    try:
        with source_engine.connect() as source_conn, dest_engine.connect() as dest_conn:
            print("✅ Connections successful.")
            
            for table_name in table_names:
                print(f"\nProcessing table: {table_name}...")
                
                # Read all data from the source table
                source_result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = source_result.fetchall()
                
                if not rows:
                    print(f"  -> No data found in {table_name}. Skipping.")
                    continue

                print(f"  -> Found {len(rows)} rows to migrate.")
                
                # Get columns and prepare for bulk insert
                columns = source_result.keys()
                dest_table = table(table_name, *[column(c) for c in columns])
                
                # Convert rows to a list of dictionaries
                rows_to_insert = [dict(row._mapping) for row in rows]
                
                # Perform a bulk insert into the destination table
                dest_conn.execute(dest_table.insert(), rows_to_insert)
                print(f"  -> Successfully migrated {len(rows)} rows to {table_name}.")

            # IMPORTANT: Commit the transaction to make all changes permanent
            dest_conn.commit()
            print("\n✅ All data migrated and committed successfully!")

    except Exception as e:
        print(f"\n🔴 An error occurred: {e}")
        print("Migration failed. The destination database was not changed.")

if __name__ == "__main__":
    migrate()