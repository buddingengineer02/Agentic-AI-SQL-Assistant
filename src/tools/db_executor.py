import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Read default configurations from environment
QUERY_TIMEOUT = float(os.getenv("QUERY_TIMEOUT", 30.0))
MAX_ROWS = int(os.getenv("MAX_ROWS", 1000))

def execute_read_query(db_path: str, sql_query: str) -> tuple[pd.DataFrame, str]:
    """
    Executes a SELECT query in read-only mode using 'PRAGMA query_only = ON'.
    Limits the output to MAX_ROWS (1000 by default) for safety.
    Returns: (DataFrame, error_message_or_empty)
    """
    conn = None
    try:
        # Establish connection with timeout
        conn = sqlite3.connect(db_path, timeout=QUERY_TIMEOUT)
        
        # Enforce read-only mode at connection level
        conn.execute("PRAGMA query_only = ON")
        
        # Run query and fetch up to MAX_ROWS rows
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Fetch description to get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(MAX_ROWS)
        
        df = pd.DataFrame(rows, columns=columns)
        return df, ""
        
    except sqlite3.OperationalError as e:
        if "query_only" in str(e) or "attempt to write" in str(e).lower():
            return pd.DataFrame(), "Security block: Attempted write operation in read-only mode."
        return pd.DataFrame(), f"Database operation error: {e}"
    except Exception as e:
        return pd.DataFrame(), f"Error running read query: {e}"
    finally:
        if conn:
            conn.close()

def execute_write_query(db_path: str, sql_query: str) -> tuple[int, str]:
    """
    Executes an INSERT or UPDATE query in normal write mode.
    Returns: (affected_rows_count, error_message_or_empty)
    """
    conn = None
    try:
        # Connect with timeout
        conn = sqlite3.connect(db_path, timeout=QUERY_TIMEOUT)
        cursor = conn.cursor()
        
        # Execute statement
        cursor.execute(sql_query)
        
        # Commit transaction
        conn.commit()
        
        # Get count of affected rows
        affected = conn.total_changes
        return affected, ""
        
    except Exception as e:
        return 0, f"Error running write query: {e}"
    finally:
        if conn:
            conn.close()
