import time
from dataclasses import dataclass
from functools import cached_property
from multiprocessing import Pool
from typing import Iterable

import psycopg
from lib.composition import Composition
from lib.db import (
    DatabaseOrCursor,
    DbChampion,
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)
from lib.utils import print_elapsed

MAX_TEAM_SIZE = 8

# PG uses really shitty query plans if this is any larger
# eg ~300ms for LIMIT 10_000 vs ~30_000ms for LIMIT 20_000
COMPS_PER_ITERATION = 10_000

db = init_db()
cursor = db.cursor()

ALL_CHAMPIONS = get_all_champions(cursor)
ALL_TRAITS = get_all_traits(cursor)
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
        SELECT COUNT(*) count
        FROM compositions c
        WHERE c.id = %s
        LIMIT 1
        """,
        [hash],
    ).fetchone()

    return bool(r) and r["count"] == 1


def insert_expansions(comps: Iterable[ExpandedComp], cursor: psycopg.Cursor):
    to_update = [ce.source for ce in comps]
    params = [cmp.hash for cmp in to_update]
    vals = ", ".join("%s" for _ in params)
    cursor.execute(
        f"""
        UPDATE compositions c
        SET is_expanded = true
        WHERE c.id IN ({vals})
        """,
        params,
    )

    to_insert = set([cmp for ce in comps for cmp in ce.expansions])
    to_insert = {cmp for cmp in to_insert if not check_comp_exists(cmp.hash, cursor)}
    with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
        for cmp in to_insert:
            r = (cmp.hash, len(cmp))
            copy.write_row(r)


def insert_comps(comps: Iterable[Composition], cursor: psycopg.Cursor):
    with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
        for cmp in comps:
            r = (cmp.hash, len(cmp))
            copy.write_row(r)


def update_is_expanded(
    comps: Iterable[Composition],
    cursor: psycopg.Cursor,
):
    params = [cmp.hash for cmp in comps]
    vals = ", ".join("%s" for _ in params)
    cursor.execute(
        f"""
        UPDATE compositions c
        SET is_expanded = true
        WHERE c.id IN ({vals})
        """,
        params,
    )


def fetch_comps_to_expand(limit: int | None = 1_000_000):
    vals = [MAX_TEAM_SIZE]
    limit_clause = ""
    if limit and limit > 0:
        limit_clause = "LIMIT %s" if limit and limit > 0 else ""
        vals.append(limit)

    rows = cursor.execute(
        f"""
        SELECT
            id,
            ARRAY_AGG(champ.id_champion) id_champs
        FROM (
            SELECT id 
            FROM compositions comp
            WHERE
                comp.is_expanded = FALSE
                AND comp.SIZE < %s
            {limit_clause}
        ) AS comp
        INNER JOIN composition_champions champ
            ON comp.id = champ.id_composition
        GROUP BY comp.id
        """,
        vals,
    ).fetchall()

    comps = [dict(**r, comp=Composition(r["id_champs"])) for r in rows]

    return comps


def main():
    has_comps = db.execute("SELECT * FROM compositions LIMIT 1").fetchone()
    if has_comps:
        print(f"Found existing comps in database, skipping initial seed phase")
    else:
        with db.transaction():
            for champ in ALL_CHAMPIONS.values():
                insert_comps([Composition([champ.id])], cursor)
        db.commit()

    while True:
        start = time.time()

        print_elapsed(start, "fetching comps")
        comps = fetch_comps_to_expand(limit=COMPS_PER_ITERATION)
        if not comps:
            break

        print_elapsed(start, "expanding")
        expanded_comps: list[ExpandedComp] = list()
        for db_comp in comps:
            cmp = db_comp["comp"]

            ce = expand_comp(cmp)
            expanded_comps.append(ce)

        print_elapsed(start, "inserting")
        with db.transaction():
            to_update = [ce.source for ce in expanded_comps]
            update_is_expanded(to_update, cursor)

            to_insert = set([cmp for ce in expanded_comps for cmp in ce.expansions])
            to_insert = {
                cmp for cmp in to_insert if not check_comp_exists(cmp.hash, cursor)
            }
            insert_comps(to_insert, cursor)

        elapsed = time.time() - start
        avg = len(comps) / elapsed
        print_elapsed(start, f"done ({avg:.1f} it/s)")


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

    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
