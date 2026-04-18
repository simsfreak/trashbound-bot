from contextlib import contextmanager
import psycopg
from config import DATABASE_URL

@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def run_schema():
    with get_conn() as conn:
        with conn.cursor() as cur:
            with open("db/schema.sql", "r", encoding="utf-8") as f:
                cur.execute(f.read())
