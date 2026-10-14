from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connect(database_url: str) -> Iterator[psycopg.Connection]:
    """One short-lived connection per request.

    Serverless functions can't hold a pool, so point DATABASE_URL at the
    Supabase transaction pooler (port 6543). prepare_threshold=None turns off
    server-side prepared statements, which the transaction pooler can't route.
    """
    with psycopg.connect(
        database_url,
        row_factory=dict_row,
        prepare_threshold=None,
        connect_timeout=5,
    ) as conn:
        # SET LOCAL, not a startup option: poolers may reject startup options,
        # and a session-level SET would leak to other clients of the pooler.
        conn.execute("set local statement_timeout = '15s'")
        yield conn
