from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def update_outreach_schema(engine: Engine) -> None:
    """
    Add Phase 6 columns to an existing SQLite database if missing.

    This is a small SQLite migration for the assignment.
    It preserves existing influencer and outreach records.
    """

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if "outreach_messages" not in table_names:
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("outreach_messages")
    }

    additions = {
        "sent_at": "DATETIME",
        "attempt_count": "INTEGER NOT NULL DEFAULT 0",
        "delivery_note": "TEXT",
    }

    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE outreach_messages "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )