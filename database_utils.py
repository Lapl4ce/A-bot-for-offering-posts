import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH
import time

@contextmanager
def get_db_connection(retries=3, delay=0.1):
    """Handle database locking with retries"""
    for i in range(retries):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
                break
            finally:
                conn.close()
        except sqlite3.OperationalError as e:
            if "database is locked" not in str(e) or i == retries - 1:
                raise
            time.sleep(delay)