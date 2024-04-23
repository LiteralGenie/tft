import psycopg
from lib.composition import Composition
from lib.db import (DbChampion, DbTrait, get_all_champions, get_all_traits,
                    get_champions_by_trait, init_db)
from tqdm import tqdm

MAX_TEAM_SIZE = 6

db = init_db()
ALL_CHAMPIONS = get_all_champions(db)
ALL_TRAITS = get_all_traits(db)
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


def check_exists(comp: Composition) -> bool:
    result = db.execute(
        """
        SELECT is_expanded FROM compositions
        WHERE hash = %s
        """,
        [comp.hash],
    ).fetchone()

    return result != None


def insert_comp(comp: Composition, cursor: psycopg.Cursor):
    id_comp = cursor.execute(
        """
        INSERT INTO compositions
            (hash, size) VALUES
            (%s, %s)
        RETURNING id;
        """,
        [comp.hash, len(comp)],
    ).fetchone()["id"]

    cursor.executemany(
        """
        INSERT INTO composition_champions
            (id_composition, id_champion) VALUES
            (%s, %s)
        """,
        [(id_comp, id_champ) for id_champ in comp.ids],
    )


def fetch_comps_to_expand(limit: int | None = 1_000_000):
    # @jank: Script seems to exit early without error if too many matching rows

    vals = [MAX_TEAM_SIZE]

    limit_clause = ""
    if limit and limit > 0:
        limit_clause = "LIMIT %s" if limit and limit > 0 else ""
        vals.append(limit)

    rows = db.execute(
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
        for champ in ALL_CHAMPIONS.values():
            insert_comp(Composition([champ.id]))
            db.commit()

    while True:
        comps = fetch_comps_to_expand(limit=1_000_000)

        if not comps:
            break

        for idx, db_comp in enumerate(tqdm(comps)):
            cursor = db.cursor()
            with db.transaction():
                cmp = db_comp["comp"]

                update = expand_comp(cmp)
                update = [cmp for cmp in update if not check_exists(cmp)]

                for new_comp in update:
                    insert_comp(new_comp, cursor)

                cursor.execute(
                    """
                    UPDATE compositions
                    SET is_expanded = true
                    WHERE id = %s
                    """,
                    [db_comp["id"]],
                )


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
