import sqlite3
import json
import datetime
import os

DB_FILE = "safewatch_db.sqlite"

def get_db_conn():
    conn = sqlite3.connect(DB_FILE)
    #make the database return dictionary-like rows
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database and creates the 'scan_log' table
    if it doesn't already exist.
    """
    try:
        # connect() will create the file if it doesn't exist
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # SQL command to create the table
        # We store violations as a JSON text string
        # 'reviewed' is a BOOLEAN (0=False, 1=True) for the dashboard
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            file_path TEXT NOT NULL,
            category TEXT,
            status TEXT NOT NULL,
            violations TEXT,
            reviewed INTEGER DEFAULT 0
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Database initialized successfully: {DB_FILE}")
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def log_scan(file_path, category, scan_result):
 
    if not isinstance(scan_result, dict):
        print(f"Error: log_scan_result received invalid scan_result: {scan_result}")
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Prepare data for insertion
        timestamp = datetime.datetime.now()
        status = scan_result.get("status", "unknown")
        violations_list = scan_result.get("violations", [])
        
        # Convert the list of violations into a JSON string for storage
        violations_json = json.dumps(violations_list)
        
        # SQL INSERT command with placeholders (?) to prevent SQL injection
        insert_sql = """
        INSERT INTO scan_log (timestamp, file_path, category, status, violations, reviewed)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        data_tuple = (timestamp, file_path, category, status, violations_json, 0)
        
        cursor.execute(insert_sql, data_tuple)
        conn.commit()

    except sqlite3.Error as e:
        print(f"Error logging to database: {e}")
    finally:
        if conn:
            conn.close()
    
def delete_log(file_path):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        sql = "DELETE FROM scan_log WHERE file_path = ?;"
        
        cursor.execute(sql, (file_path,))
        conn.commit()
        
        print(f"  Deleted log entries for: {file_path}")

    except sqlite3.Error as e:
        print(f"  Error deleting log for {file_path}: {e}")
    finally:
        if conn:
            conn.close()

def get_all_logs():
    """Fetches all scan logs, ordered to show unreviewed danger first."""
    logs = []
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        # This query puts unreviewed items first, then by 'danger', then most recent
        query = """
            SELECT id, timestamp, file_path, category, status, violations, reviewed
            FROM scan_log
            ORDER BY reviewed ASC
        """
        cursor.execute(query)
        logs = cursor.fetchall() # fetchall() returns a list of sqlite3.Row objects
    except sqlite3.Error as e:
        print(f"Error fetching logs from database: {e}")
    finally:
        if conn:
            conn.close()
    return logs

def mark_as_reviewed(log_id):
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        sql = "UPDATE scan_log SET reviewed = 1 WHERE id = ?"
        cursor.execute(sql, (log_id,))
        conn.commit()
        print(f"Marked log ID {log_id} as reviewed.")
        return True
    except sqlite3.Error as e:
        print(f"Error updating log ID {log_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

# --- Main execution ---
if __name__ == "__main__":
    print("Running database initialization...")
    init_db()