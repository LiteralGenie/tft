import time

from lib.db import get_all_champions, init_db
from lib.utils import print_elapsed
from psycopg import Cursor

db = init_db()
cursor = db.cursor()

ALL_CHAMPIONS = get_all_champions(cursor)


def fetch_missing(limit=1_000_000):
    rows = db.execute(
        """
        SELECT id
        FROM compositions c
        WHERE c.has_champions = false
        LIMIT %s
        """,
        [limit],
    )

    return [r["id"] for r in rows]


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

    vals = ", ".join("%s" for _ in hashes)
    cursor.execute(
        f"""
        UPDATE compositions
        SET has_champions = true
        WHERE id IN ({vals})
        """,
        hashes,
    )


def main():
    while True:
        start = time.time()

        print_elapsed(start, "fetching")
        missing = fetch_missing()
        if not missing:
            break

        print_elapsed(start, f"inserting {len(missing):,} rows")
        with db.transaction():
            insert_comp_champs(missing, cursor)

        elapsed = time.time() - start
        avg = len(missing) / elapsed
        print_elapsed(start, f"done ({avg:.1f} it/s)")


if __name__ == "__main__":
    main()
