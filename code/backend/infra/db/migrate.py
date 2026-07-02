"""Lightweight migration runner for Verra.

Applies schema.sql and numbered migrations from infra/db/migrations/.
Requires psycopg (v3): pip install psycopg[binary]

Usage:
    DATABASE_URL=postgres://verra:verra@localhost:5432/verra python migrate.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import psycopg

SCHEMA_FILE = Path(__file__).with_name("schema.sql")
MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def ensure_migrations_table(cur: psycopg.Cursor) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)


def already_applied(cur: psycopg.Cursor, filename: str) -> bool:
    cur.execute("SELECT 1 FROM schema_migrations WHERE filename = %s", (filename,))
    return cur.fetchone() is not None


def apply_file(cur: psycopg.Cursor, path: Path) -> None:
    sql = path.read_text()
    # Split on statement terminators to get better error messages.
    statements = [s.strip() for s in re.split(r";\s*$", sql, flags=re.MULTILINE) if s.strip()]
    for statement in statements:
        cur.execute(statement)


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "postgres://verra:verra@localhost:5432/verra")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            print(f"Applying {SCHEMA_FILE.name}...")
            apply_file(cur, SCHEMA_FILE)

            ensure_migrations_table(cur)

            if MIGRATIONS_DIR.exists():
                for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
                    if already_applied(cur, migration.name):
                        print(f"Skipping {migration.name} (already applied)")
                        continue
                    print(f"Applying {migration.name}...")
                    apply_file(cur, migration)
                    cur.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (%s)",
                        (migration.name,),
                    )

        conn.commit()
    print("Migrations complete.")


if __name__ == "__main__":
    main()
