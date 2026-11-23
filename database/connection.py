import sqlite3
from pathlib import Path

from config import DATABASE_PATH


def connect(db_path=None):
    path = Path(db_path or DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path=None):
    connection = connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS service_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_name TEXT,
                operation TEXT NOT NULL,
                previous_state TEXT,
                new_state TEXT,
                result TEXT NOT NULL,
                error_details TEXT
            );
            CREATE TABLE IF NOT EXISTS service_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_name TEXT NOT NULL,
                failure_type TEXT NOT NULL,
                details TEXT,
                active_state TEXT,
                sub_state TEXT
            );
            CREATE TABLE IF NOT EXISTS recovery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                service_name TEXT NOT NULL,
                attempt_number INTEGER NOT NULL,
                result TEXT NOT NULL,
                previous_state TEXT,
                new_state TEXT,
                details TEXT
            );
            """
        )
        connection.commit()
    finally:
        connection.close()
