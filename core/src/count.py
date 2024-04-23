import time
from dataclasses import dataclass
from functools import cached_property
from multiprocessing import Pool
from typing import Iterable

import psycopg
from lib.composition import Composition
from lib.db import (
    DbChampion,
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)
from lib.utils import print_elapsed, to_batch_size, to_n_batches
from tqdm import tqdm

MAX_TEAM_SIZE = 8

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

    def __hash__(self) -> int:
        return hash(tuple(self.hashes))

    def __eq__(self, value: object) -> bool:
        return hash(value) == hash(self)


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


def insert_comps(comps: Iterable[Composition], cursor: psycopg.Cursor):
    start = time.time()
    to_insert = set()
    for c in comps:
        r = cursor.execute(
            """
            SELECT COUNT(*) count
            FROM compositions c
            WHERE c.id = %s
            LIMIT 1
            """,
            [c.hash],
        ).fetchone()

        if r and r["count"] == 0:
            to_insert.add(c)
    print_elapsed(start, "done filtering to_insert")

    comp_data = [(comp.hash, len(comp)) for comp in to_insert]
    with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
        for d in comp_data:
            copy.write_row(d)
    print_elapsed(start, "done copy comps")

    champ_data = [(comp.hash, id_champ) for comp in to_insert for id_champ in comp.ids]
    with cursor.copy(
        "COPY composition_champions (id_composition, id_champion) FROM STDIN"
    ) as copy:
        for d in champ_data:
            copy.write_row(d)
    print_elapsed(start, "done copy comp_champs")


def insert_comp(
    source: Composition,
    expansions: Iterable[Composition],
    cursor: psycopg.Cursor,
):
    cursor.execute(
        f"""
        UPDATE compositions
        SET is_expanded = true
        WHERE id = %s
        """,
        [source.hash],
    )

    to_insert = set()
    for c in expansions:
        r = cursor.execute(
            """
            SELECT COUNT(*) count
            FROM compositions c
            WHERE c.id = %s
            LIMIT 1
            """,
            [c.hash],
        ).fetchone()

        if r and r["count"] == 0:
            to_insert.add(c)

    with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
        for comp in to_insert:
            d = (comp.hash, len(comp))
            copy.write_row(d)

    champ_data = [(comp.hash, id_champ) for comp in to_insert for id_champ in comp.ids]
    with cursor.copy(
        "COPY composition_champions (id_composition, id_champion) FROM STDIN"
    ) as copy:
        for d in champ_data:
            copy.write_row(d)


def insert_expansions(updates: list[ExpandedComp]):
    db = init_db()
    cursor = db.cursor()

    with db.transaction():
        for x in updates:
            insert_comp(x.source, x.expansions, cursor)

    return len(updates)


def fetch_comps_to_expand(limit: int | None = 1_000_000):
    # @jank: Script seems to exit early without error if too many matching rows

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
        FROM compositions comp
        INNER JOIN composition_champions champ
            ON comp.id = champ.id_composition
        WHERE 
            comp.is_expanded = false
            AND comp.size < %s
        GROUP BY comp.id
        {limit_clause}
        """,
        vals,
    ).fetchall()

    comps = [dict(**r, comp=Composition(r["id_champs"])) for r in rows]

    return comps


def create_batch(updates: set[ExpandedComp], size: int) -> list[ExpandedComp]:
    comps = iter(updates)

    batch = [next(comps)]
    hashes_in_batch = [*batch[0].hashes]

    for c in comps:
        if len(batch) >= size:
            break

        if any(h in hashes_in_batch for h in c.hashes):
            continue

        batch.append(c)
        hashes_in_batch.extend(c.hashes)

    for c in batch:
        updates.remove(c)

    return batch


def main():
    comp_count = db.execute("SELECT * FROM compositions LIMIT 1").fetchone()
    if comp_count:
        print(f"Found existing comps in database, skipping initial seed phase")
    else:
        with db.transaction():
            for champ in ALL_CHAMPIONS.values():
                insert_comps([Composition([champ.id])], cursor)
        db.commit()

    n_workers = 8
    with Pool(n_workers) as pool:
        while True:
            comps = fetch_comps_to_expand(limit=10_000)
            if not comps:
                break

            to_insert: set[ExpandedComp] = set()
            for db_comp in comps:
                cmp = db_comp["comp"]

                expanded = expand_comp(cmp)
                to_insert.add(expanded)

            with tqdm(total=len(to_insert)) as pbar:
                while True:
                    if not to_insert:
                        break

                    batch = create_batch(to_insert, 1_00)
                    # seen = set()
                    # for ec in batch:
                    #     assert not any(h in seen for h in ec.hashes)
                    #     seen.update(ec.hashes)

                    sub_batches = to_n_batches(batch, n_workers)

                    for count in pool.imap_unordered(insert_expansions, sub_batches):
                        pbar.update(count)


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
