import logging
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL

logger = logging.getLogger(__name__)


def get_connection():
    """Open a new psycopg connection using the configured DATABASE_URL."""
    # Use explicit keyword to avoid conninfo parsing surprises.
    try:
        return psycopg.connect(conninfo=DATABASE_URL, row_factory=dict_row)  # type: ignore[arg-type]
    except Exception as e:
        logger.exception("Database connection failed")
        raise RuntimeError(f"Database connection failed: {e}") from e


def fetch_one(sql, params=None):
    """Execute a query and return a single row as a dict (commits if needed)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.fetchone()
    except Exception as e:
        logger.exception("Database query failed")
        raise RuntimeError(f"Database query failed: {e}") from e
    finally:
        conn.close()


def fetch_all(sql, params=None):
    """Execute a query and return all rows as dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception as e:
        logger.exception("Database query failed")
        raise RuntimeError(f"Database query failed: {e}") from e
    finally:
        conn.close()


def fetch_k(sql, k=1, params=None):
    """Execute a query and return at most k rows as dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchmany(k)
    except Exception as e:
        logger.exception("Database query failed")
        raise RuntimeError(f"Database query failed: {e}") from e
    finally:
        conn.close()


def execute(sql, params=None):
    """Execute a statement and return the affected row count."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
    except Exception as e:
        logger.exception("Database execution failed")
        raise RuntimeError(f"Database execution failed: {e}") from e
    finally:
        conn.close()


def execute_many(sql, params_seq):
    """Execute a statement for many parameter sets and return affected row count."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, params_seq)
            conn.commit()
            return cur.rowcount
    except Exception as e:
        logger.exception("Database execution failed")
        raise RuntimeError(f"Database execution failed: {e}") from e
    finally:
        conn.close()


def fetch_value(sql, params=None):
    """Execute a query and return the first column of the first row."""
    row = fetch_one(sql, params)
    if row is None:
        return None
    if isinstance(row, dict):
        for value in row.values():
            return value
        return None
    return row[0]


def fetch_one_required(sql, params=None):
    """Execute a query and return a single row, raising if none found."""
    row = fetch_one(sql, params)
    if row is None:
        raise RuntimeError("Database query returned no rows")
    return row


@contextmanager
def transaction():
    """Yield a cursor inside a transaction (commit on success, rollback on error)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.exception("Database transaction failed")
        raise RuntimeError(f"Database transaction failed: {e}") from e
    finally:
        conn.close()


def ping():
    """Return True if a simple SELECT succeeds."""
    row = fetch_one("SELECT 1 AS ok;")
    if row is None:
        return False
    if isinstance(row, dict):
        return row.get("ok") == 1
    try:
        return row[0] == 1
    except Exception:
        return False
