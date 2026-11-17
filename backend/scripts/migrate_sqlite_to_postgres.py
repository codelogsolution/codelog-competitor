"""Copy existing KOMP rows from a legacy SQLite file into an empty PostgreSQL DB.

Run after Alembic has created the PostgreSQL schema. This utility never deletes
or modifies the SQLite source. Keep a verified backup before running it.
"""
import os
import sys
from pathlib import Path

from sqlalchemy import Integer, MetaData, create_engine, func, select, text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

TABLES = ("evidence", "battlecards", "agent_runs", "source_imports", "audit_logs")


def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    source_path = Path(os.environ.get("KOMP_SQLITE_SOURCE", "backend/data/komp.db")).resolve()
    target_url = os.environ.get("DATABASE_URL", "").strip()
    if not source_path.is_file():
        raise SystemExit(f"SQLite source not found: {source_path}")
    if not target_url:
        raise SystemExit("Set DATABASE_URL to the PostgreSQL destination first.")
    parsed = make_url(target_url)
    if parsed.drivername == "postgresql":
        target_url = target_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif parsed.drivername != "postgresql+psycopg":
        raise SystemExit("Destination DATABASE_URL must be PostgreSQL using psycopg.")

    source = create_engine(f"sqlite:///{source_path}")
    target = create_engine(target_url, pool_pre_ping=True)
    source_meta, target_meta = MetaData(), MetaData()
    source_meta.reflect(bind=source)
    target_meta.reflect(bind=target)
    missing = [name for name in TABLES if name not in target_meta.tables]
    if missing:
        raise SystemExit(f"PostgreSQL schema is missing {missing}; run Alembic upgrade first.")
    with target.connect() as connection:
        counts = {name: connection.scalar(select(func.count()).select_from(target_meta.tables[name])) for name in TABLES}
    occupied = {name: count for name, count in counts.items() if count}
    if occupied:
        raise SystemExit(f"Refusing to mix legacy data into non-empty PostgreSQL tables: {occupied}")

    copied = {}
    with source.connect() as src, target.begin() as dst:
        for name in TABLES:
            if name not in source_meta.tables:
                copied[name] = 0
                continue
            src_table, dst_table = source_meta.tables[name], target_meta.tables[name]
            destination_columns = set(dst_table.c.keys())
            rows = src.execute(select(src_table)).mappings().all()
            payload = [
                {key: value for key, value in row.items() if key in destination_columns}
                for row in rows
            ]
            if payload:
                dst.execute(dst_table.insert(), payload)
            copied[name] = len(payload)

        for name in TABLES:
            table = target_meta.tables[name]
            if "id" not in table.c or not isinstance(table.c.id.type, Integer):
                continue
            dst.execute(text(
                "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                "GREATEST(COALESCE((SELECT MAX(id) FROM \"" + name + "\"), 1), 1), "
                "EXISTS (SELECT 1 FROM \"" + name + "\"))"
            ), {"table_name": name})

    print("Copied legacy KOMP rows:")
    for name, count in copied.items():
        print(f"  {name}: {count}")
    print("The SQLite source remains unchanged. Copy the UPLOAD_DIR files separately if any source imports exist.")
    source.dispose()
    target.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
