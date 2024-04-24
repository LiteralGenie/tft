import time

from lib.composition import Composition
from lib.db import get_all_champions, init_db
from lib.utils import print_elapsed
from psycopg import Cursor

db = init_db()
cursor = db.cursor()

ALL_CHAMPIONS = get_all_champions(cursor)


def fetch_missing(limit=30_000):
    rows = db.execute(
        """
        SELECT id FROM (
            SELECT id, SUM(CASE WHEN cc.id_champion IS NULL THEN 1 ELSE 0 END) null_count FROM compositions c
            LEFT JOIN composition_champions cc 
                ON cc.id_composition = c.id
            GROUP BY c.id
        )
        WHERE null_count > 0
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


def main():
    while True:
        start = time.time()

        print_elapsed(start, "fetching")
        missing = fetch_missing()
        if not missing:
            break

        print_elapsed(start, "inserting")
        with db.transaction():
            insert_comp_champs(missing, cursor)

        elapsed = time.time() - start
        avg = len(missing) / elapsed
        print_elapsed(start, f"done ({avg:.1f} it/s)")


if __name__ == "__main__":
    main()
