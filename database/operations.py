from datetime import datetime, timezone

from database.connection import connect, initialize_database


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_activity(service_name, operation, previous_state, new_state, result, error_details=None, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        connection.execute(
            """INSERT INTO service_activity
               (timestamp, service_name, operation, previous_state, new_state, result, error_details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (timestamp(), service_name, operation, previous_state, new_state, result, error_details),
        )
        connection.commit()
    finally:
        connection.close()


def save_failure(service_name, failure_type, details=None, active_state=None, sub_state=None, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        connection.execute(
            """INSERT INTO service_failures
               (timestamp, service_name, failure_type, details, active_state, sub_state)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (timestamp(), service_name, failure_type, details, active_state, sub_state),
        )
        connection.commit()
    finally:
        connection.close()


def save_recovery_attempt(service_name, attempt_number, result, previous_state=None,
                          new_state=None, details=None, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        connection.execute(
            """INSERT INTO recovery_history
               (timestamp, service_name, attempt_number, result, previous_state, new_state, details)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (timestamp(), service_name, attempt_number, result, previous_state, new_state, details),
        )
        connection.commit()
    finally:
        connection.close()


def recent_activity(limit=50, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM service_activity ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]
    finally:
        connection.close()


def recent_failures(limit=50, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM service_failures ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]
    finally:
        connection.close()


def recent_recovery_attempts(limit=50, db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM recovery_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]
    finally:
        connection.close()


def historical_summary(db_path=None):
    initialize_database(db_path)
    connection = connect(db_path)
    try:
        counts = {}
        for table in ("service_activity", "service_failures", "recovery_history"):
            counts[table] = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        return counts
    finally:
        connection.close()
