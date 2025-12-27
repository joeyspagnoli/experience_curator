import logging
import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL

logger = logging.getLogger(__name__)


def get_connection():
    # Use explicit keyword to avoid conninfo parsing surprises.
    try:
        return psycopg.connect(conninfo=DATABASE_URL, row_factory=dict_row)  # type: ignore[arg-type]
    except Exception as e:
        logger.exception("Database connection failed")
        raise RuntimeError(f"Database connection failed: {e}") from e


def fetch_one(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    except Exception as e:
        logger.exception("Database query failed")
        raise RuntimeError(f"Database query failed: {e}") from e
    finally:
        conn.close()


def fetch_all(sql, params=None):
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


def ping():
    row = fetch_one("SELECT 1 AS ok;")
    if row is None:
        return False
    if isinstance(row, dict):
        return row.get("ok") == 1
    try:
        return row[0] == 1
    except Exception:
        return False
