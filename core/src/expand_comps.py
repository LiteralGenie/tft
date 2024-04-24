import asyncio
import time
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable

import psycopg
from lib.composition import Composition
from lib.db import (
    DB_URL,
    DatabaseOrCursor,
    DbChampion,
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)
from lib.utils import print_elapsed
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

MAX_TEAM_SIZE = 8
COMPS_PER_ITERATION = 20_000

_db = init_db()
_cursor = _db.cursor()

ALL_CHAMPIONS = get_all_champions(_cursor)
ALL_TRAITS = get_all_traits(_cursor)
CHAMPIONS_BY_TRAIT = get_champions_by_trait(ALL_CHAMPIONS.values())


@dataclass
class ExpandedComp:
    source: Composition
    expansions: list[Composition]

    @cached_property
    def hashes(self):
        return [self.source.hash] + [c.hash for c in self.expansions]


def get_comp_traits(comp: Composition) -> set[DbTrait]:
    champs = [ALL_CHAMPIONS[id] for id in comp.ids]

    traits: set[DbTrait] = set()
    for champ in champs:
        for id in champ.traits:
            traits.add(ALL_TRAITS[id])

    return traits


def expand_comp(comp: Composition) -> ExpandedComp:
    traits = get_comp_traits(comp)

    candidates: set[DbChampion] = set()
    for t in traits:
        for c in CHAMPIONS_BY_TRAIT[t.id]:
            if c.id not in comp.ids:
                candidates.add(c)

    expansions = [comp.add(c.id) for c in candidates]
    return ExpandedComp(source=comp, expansions=expansions)


def check_comp_exists(hash: str, cursor: DatabaseOrCursor) -> bool:
    r = cursor.execute(
        """
        SELECT 1
        FROM compositions c
        WHERE c.id = %s
        """,
        [hash],
    ).fetchone()

    return bool(r)


async def insert_comps(comps: Iterable[Composition], conn: psycopg.AsyncConnection):
    async with conn.cursor() as cursor:
        async with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
            for cmp in comps:
                await copy.write_row((cmp.hash, len(cmp)))


async def delete_todos(conn: psycopg.AsyncConnection, expanded: Iterable[Composition]):
    async with conn.cursor() as cursor:
        await cursor.executemany(
            """
            DELETE FROM needs_expansion
            WHERE id_composition = %s
            """,
            [(c.hash,) for c in expanded],
        )


async def fetch_comps_to_expand(conn: psycopg.AsyncConnection, limit: int):
    vals = [MAX_TEAM_SIZE]
    limit_clause = ""
    if limit and limit > 0:
        limit_clause = "LIMIT %s" if limit and limit > 0 else ""
        vals.append(limit)

    rows = await (
        await conn.execute(
            f"""
        SELECT c.id
        FROM compositions c
        INNER JOIN needs_expansion ne
            ON ne.id_composition = c.id
        WHERE c.size < %s
        {limit_clause}
        """,
            vals,
        )
    ).fetchall()

    comps = [
        dict(
            **r,
            # Infer champions from hash instead of JOIN so we don't have to wait on the init_comp_champs script
            comp=Composition([int(id) for id in r["id"].split(",")]),
        )
        for r in rows
    ]

    return comps


async def create_temp_insertion(conn: psycopg.AsyncConnection):
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS temp_expand (
            id      TEXT        PRIMARY KEY,
            size    INTEGER     NOT NULL
        )
        """
    )

    await conn.execute("TRUNCATE temp_expand")


async def insert_temp(conn: psycopg.AsyncConnection, comps: Iterable[Composition]):
    async with conn.cursor() as cursor:
        async with cursor.copy("COPY temp_expand (id, size) FROM STDIN") as copy:
            for cmp in comps:
                await copy.write_row((cmp.hash, len(cmp)))


async def dedupe_temp(conn: psycopg.AsyncConnection):
    await conn.execute(
        """
        DELETE FROM temp_expand te
        USING compositions c
        WHERE c.id = te.id
        """
    )


async def merge_temp(conn: psycopg.AsyncConnection):
    await conn.execute(
        """
        INSERT INTO compositions (id, size)
        SELECT te.id, te.size
        FROM temp_expand te
        """
    )

    await conn.execute(
        """
        INSERT INTO needs_champions (id_composition)
        SELECT te.id
        FROM temp_expand te
        """
    )

    await conn.execute(
        """
        INSERT INTO needs_expansion (id_composition)
        SELECT te.id
        FROM temp_expand te
        """
    )


async def truncate_temp(conn: psycopg.AsyncConnection):
    await conn.execute("TRUNCATE temp_expand")


async def process_expansions(
    conn: psycopg.AsyncConnection,
    to_insert: list[Composition] | None = None,
    to_delete: list[Composition] | None = None,
):
    async with conn.transaction():
        if to_delete:
            await delete_todos(conn, to_delete)

        if to_insert:
            await insert_temp(conn, to_insert)
            await dedupe_temp(conn)
            await merge_temp(conn)
            await truncate_temp(conn)


async def calculate_updates(conn: psycopg.AsyncConnection) -> dict:
    db_comps = await fetch_comps_to_expand(conn, limit=COMPS_PER_ITERATION)

    expanded_comps: list[ExpandedComp] = list()
    for db_comp in db_comps:
        cmp = db_comp["comp"]

        ce = expand_comp(cmp)
        expanded_comps.append(ce)

    to_insert = set([cmp for ce in expanded_comps for cmp in ce.expansions])
    to_delete = [ce.source for ce in expanded_comps]

    return dict(to_insert=to_insert, to_delete=to_delete)


async def main():
    async with AsyncConnectionPool(DB_URL, kwargs={"row_factory": dict_row}) as pool:
        async with pool.connection() as conn:
            # Seed comps-to-expand
            has_comps = await (
                await conn.execute("SELECT * FROM compositions LIMIT 1")
            ).fetchone()
            if has_comps:
                print(f"Found existing comps in database, skipping initial seed phase")
            else:
                async with conn.transaction():
                    for champ in ALL_CHAMPIONS.values():
                        await insert_comps([Composition([champ.id])], conn)

            # Create temporary table for insertions (bc they need to be existence-checked)
            async with conn.transaction():
                await create_temp_insertion(conn)
                await truncate_temp(conn)

            updates = dict()
            while True:
                start = time.time()
                num_expanded = len(updates.get("to_delete", []))
                num_created = len(updates.get("to_insert", []))

                print_elapsed(
                    start,
                    f"processing {num_expanded:,} comps that were expanded to {num_created:,} new comps",
                )
                [_, updates] = await asyncio.gather(
                    process_expansions(conn, **updates),
                    calculate_updates(conn),
                )

                elapsed = time.time() - start
                avg = num_expanded / elapsed
                print_elapsed(start, f"done ({avg:.1f} expansions/s)")

                if not updates:
                    break


if __name__ == "__main__":
    # """
    # @todo: This script is bottlenecked at 2~2.5k compositions / sec by sqlite stuff.
    #        Specifically the check-if-comp-exists and insert-new-comp queries.
    #          The existence query is already indexed.
    #          Running off a ramdisk doesn't help much (maybe <10% faster)

    #        Considering the number of possible comps looks like this
    #          size   count
    #             1	        60
    #             2	       317
    #             3	     2,272
    #             4	    18,275
    #             5	   152,422
    #             6    1,260,036
    #             7   10,055,919
    #             8   76,112,903
    #        That is way too slow. That implies it'll take <3 hours to calculate comps of size 8 and another <18 hours for size 9.

    #        Postgres might help but probably need to containerize everything first (including devcontainer).
    #        Also would make testing a pain.

    #        And just for reference, the db eats up ~40 GB on disk (~10 GB gzipped) for up to size 8.
    # """

    # import cProfile
    # from pstats import SortKey

    # cProfile.run("main()", sort=SortKey.CUMULATIVE)

    asyncio.run(main())
