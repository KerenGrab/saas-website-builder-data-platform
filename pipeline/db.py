"""PostgreSQL connection and schema-inspection utilities."""

import psycopg
from psycopg import sql

from pipeline import config


TARGET_SCHEMA = "public"


def _validate_credentials():
    if not config.DB_USER:
        raise RuntimeError(
            "DB_USER is not configured "
            "in the environment variables."
        )

    if not config.DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is not configured "
            "in the environment variables."
        )


def open_connection(*, autocommit=False):
    """Open a connection to the existing canonical PostgreSQL database."""
    _validate_credentials()

    return psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        connect_timeout=5,
        autocommit=autocommit,
    )


def check_connection():
    """Verify connectivity without modifying PostgreSQL."""
    connection = open_connection(
        autocommit=True
    )

    connection.close()


def validate_target_tables_exist(
    connection,
    target_tables,
):
    """Verify that all 49 Part 8 target tables already exist."""
    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            """,
            (TARGET_SCHEMA,),
        )

        existing_tables = {
            row[0]
            for row in cursor.fetchall()
        }

    missing_tables = sorted(
        set(target_tables)
        - existing_tables
    )

    if missing_tables:
        raise RuntimeError(
            "Canonical PostgreSQL target schema "
            "is incomplete. "
            f"Missing tables: {missing_tables}"
        )


def get_target_table_columns(
    connection,
    table_name,
):
    """Return target columns in physical ordinal order."""
    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                column_name,
                is_nullable,
                column_default,
                is_generated,
                identity_generation,
                data_type
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (
                TARGET_SCHEMA,
                table_name,
            ),
        )

        rows = cursor.fetchall()

    if not rows:
        raise RuntimeError(
            f"Target table "
            f"'{TARGET_SCHEMA}.{table_name}' "
            "does not exist or exposes no columns."
        )

    return [
        {
            "name": row[0],
            "nullable": row[1] == "YES",
            "default": row[2],
            "generated": row[3],
            "identity_generation": row[4],
            "data_type": row[5],
        }
        for row in rows
    ]


def run_atomic(
    connection,
    work,
    *,
    before_commit=None,
):
    """Run work(connection) inside one explicit PostgreSQL transaction.

    The connection must use autocommit=True so connection.transaction() owns
    the full boundary.  Any exception from work or before_commit causes the
    transaction context to roll back.
    """
    if not connection.autocommit:
        raise RuntimeError(
            "Atomic work requires a connection opened with autocommit=True."
        )

    with connection.transaction():
        result = work(connection)

        if before_commit is not None:
            before_commit(connection)

    return result


def get_table_count(
    connection,
    table_name,
):
    """Read COUNT(*) from one safely composed target identifier."""
    query = sql.SQL(
        "SELECT COUNT(*) FROM {}"
    ).format(
        sql.Identifier(
            TARGET_SCHEMA,
            table_name,
        )
    )

    with connection.cursor() as cursor:

        cursor.execute(query)

        return cursor.fetchone()[0]


def get_table_counts(
    connection,
    target_tables,
):
    """Return current row counts for the requested target tables."""
    return {
        table_name: get_table_count(
            connection,
            table_name,
        )
        for table_name in target_tables
    }