import time
from typing import Iterable

import psycopg
from lib.composition import Composition
from lib.db import (DbChampion, DbTrait, get_all_champions, get_all_traits,
                    get_champions_by_trait, init_db)
from lib.utils import batch_queries, print_elapsed, to_batch_size
from tqdm import tqdm

MAX_TEAM_SIZE = 7

db = init_db()
cursor = db.cursor()

ALL_CHAMPIONS = get_all_champions(cursor)
ALL_TRAITS = get_all_traits(cursor)
CHAMPIONS_BY_TRAIT = get_champions_by_trait(ALL_CHAMPIONS.values())


def get_comp_traits(comp: Composition) -> set[DbTrait]:
    champs = [ALL_CHAMPIONS[id] for id in comp.ids]

    traits: set[DbTrait] = set()
    for champ in champs:
        for id in champ.traits:
            traits.add(ALL_TRAITS[id])

    return traits


def expand_comp(comp: Composition) -> list[Composition]:
    traits = get_comp_traits(comp)

    candidates: set[DbChampion] = set()
    for t in traits:
        for c in CHAMPIONS_BY_TRAIT[t.id]:
            if c.id not in comp.ids:
                candidates.add(c)

    return [comp.add(c.id) for c in candidates]


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
            [c.hash]
        ).fetchone()

        if r and r['count'] == 0:
            to_insert.add(c)
    print_elapsed(start, 'done filtering to_insert')

    comp_data = [(comp.hash, len(comp)) for comp in to_insert]
    with cursor.copy("COPY compositions (id, size) FROM STDIN") as copy:
        for d in comp_data:
            copy.write_row(d)
    print_elapsed(start, 'done copy comps')

    champ_data = [(comp.hash, id_champ) for comp in to_insert for id_champ in comp.ids]
    with cursor.copy("COPY composition_champions (id_composition, id_champion) FROM STDIN") as copy:
        for d in champ_data:
            copy.write_row(d)
    print_elapsed(start, 'done copy comp_champs')


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

    comps = [
        dict(**r, comp=Composition(r['id_champs']))
        for r in rows
    ]

    return comps


def main():
    comp_count = db.execute("SELECT * FROM compositions LIMIT 1").fetchone()
    if comp_count:
        print(f"Found existing comps in database, skipping initial seed phase")
    else:
        with db.transaction():
            for champ in ALL_CHAMPIONS.values():
                insert_comps([Composition([champ.id])], cursor)
        db.commit()

    while True:
        missing = fetch_comps_to_expand(limit=100_000)
        if not missing:
            break
        
        with tqdm(total=len(missing)) as pbar:
            comp_batches = to_batch_size(missing, 2_000)

            for comps in comp_batches:
                to_insert = set()
                for db_comp in comps:
                    cmp = db_comp["comp"]

                    update = expand_comp(cmp)
                    to_insert.update(update)

                with db.transaction():
                    insert_comps(to_insert, cursor)

                    params = [db_comp['id'] for db_comp in comps]
                    val = ', '.join('%s' for _ in params)
                    cursor.execute(
                        f"""
                        UPDATE compositions
                        SET is_expanded = true
                        WHERE id in ({val})
                        """,
                        params,
                    )

                    pbar.update(len(comps))


if __name__ == "__main__":
    """
    @todo: This script is bottlenecked at 2~2.5k compositions / sec by sqlite stuff.
           Specifically the check-if-comp-exists and insert-new-comp queries.
             The existence query is already indexed.
             Running off a ramdisk doesn't help much (maybe <10% faster)
           
           Considering the number of possible comps looks like this
             size   count
                1	        60
                2	       317
                3	     2,272
                4	    18,275
                5	   152,422
                6    1,260,036
                7   10,055,919
                8   76,112,903
           That is way too slow. That implies it'll take <3 hours to calculate comps of size 8 and another <18 hours for size 9.
            
           Postgres might help but probably need to containerize everything first (including devcontainer).
           Also would make testing a pain.

           And just for reference, the db eats up ~40 GB on disk (~10 GB gzipped) for up to size 8.
    """

    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
