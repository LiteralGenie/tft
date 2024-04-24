import time

from lib.db import get_all_champions, init_db
from lib.utils import print_elapsed
from psycopg import Cursor

db = init_db()
cursor = db.cursor()

ALL_CHAMPIONS = get_all_champions(cursor)


def fetch_missing(limit=50_000):
    rows = db.execute(
        """
        SELECT id_composition
        FROM needs_champions c
        LIMIT %s
        """,
        [limit],
    )

    return [r["id_composition"] for r in rows]


def insert_comp_champs(hashes: list[str], cursor: Cursor):
    params: list[tuple[str, int]] = []
    for hash in hashes:
        ids = [int(id) for id in hash.split(",")]

        for id in ids:
            params.append((hash, id))

    with cursor.copy(
        "COPY composition_champions (id_composition, id_champion) FROM STDIN"
    ) as copy:
        for p in params:
            copy.write_row(p)


def delete_todos(hashes: list[str], cursor: Cursor):
    cursor.executemany(
        f"""
        DELETE FROM needs_champions
        WHERE id_composition = %s
        """,
        [(h,) for h in hashes],
    )


def main():
    while True:
        start = time.time()

        print_elapsed(start, "fetching")
        missing = fetch_missing()
        if not missing:
            break

        with db.transaction():
            print_elapsed(start, f"inserting {len(missing):,} rows")
            insert_comp_champs(missing, cursor)

            print_elapsed(start, f"deleting todos")
            delete_todos(missing, cursor)

        elapsed = time.time() - start
        avg = len(missing) / elapsed
        print_elapsed(start, f"done ({avg:.1f} it/s)")


if __name__ == "__main__":
    main()
