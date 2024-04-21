import time
from typing import TypeAlias

from lib.db import (
    DbChampion,
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)
from lib.utils import group_by, print_elapsed

Composition: TypeAlias = tuple[int, ...]

MAX_TEAM_SIZE = 4

db = init_db()
ALL_CHAMPIONS = get_all_champions(db)
ALL_TRAITS = get_all_traits(db)
CHAMPIONS_BY_TRAIT = get_champions_by_trait(ALL_CHAMPIONS.values())


def get_comp_traits(comp: Composition) -> set[DbTrait]:
    champs = [ALL_CHAMPIONS[id] for id in comp]

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
            if c.id not in comp:
                candidates.add(c)

    return [comp + (c.id,) for c in candidates]


def find_comps(
    init: Composition,
    # Skip gets mutated for efficiency
    skip: set[Composition],
) -> set[Composition]:
    comps: dict[int, Composition] = {hash(init): init}
    prev: dict[int, Composition] = {hash(init): init}

    iterations = MAX_TEAM_SIZE - len(init)

    start = time.time()
    for idx in range(iterations):
        update: dict[int, Composition] = dict()
        cache_hits = 0

        for cmp in prev.values():
            if cmp in skip:
                cache_hits += 1
                continue

            skip.add(cmp)

            expansions = expand_comp(cmp)

            for expanded in expansions:
                update[hash(expanded)] = expanded
                comps[hash(expanded)] = expanded

        prev = update
        print_elapsed(
            start,
            f"Expanded to size {idx + len(init) + 1} with {cache_hits} cache_hits",
        )

    return set(comps.values())


def insert_comp(comp: Composition):
    id_comp = db.execute(
        """
        INSERT INTO compositions DEFAULT VALUES
        RETURNING id;
        """
    ).fetchone()["id"]

    db.executemany(
        """
        INSERT INTO composition_champions
            (id_composition, id_champion) VALUES
            (?, ?)
        """,
        [(id_comp, id_champ) for id_champ in comp],
    )


def main():
    comp_count = db.execute("SELECT COUNT(*) count FROM compositions").fetchone()[
        "count"
    ]
    if comp_count != 0:
        print(
            f"Found {comp_count:,} existing comps in database, skipping initial seed phase"
        )
    else:
        for champ in ALL_CHAMPIONS.values():
            insert_comp((champ.id,))
            db.commit()

    rows = db.execute(
        """
        SELECT
            id,
            comp.is_expanded,
            GROUP_CONCAT(champ.id_champion) id_champs
        FROM compositions comp
        INNER JOIN composition_champions champ
            ON comp.id = champ.id_composition
        GROUP BY comp.id
        """
    ).fetchall()

    comps = [dict(r) for r in rows]
    for new_comp in comps:
        new_comp["id_champs"] = tuple(
            int(id) for id in new_comp["id_champs"].split(",")
        )

    tmp = group_by(comps, lambda c: "to_check" if not c["is_expanded"] else "to_skip")
    to_check = tmp.get("to_check", [])
    to_skip: set[Composition] = set(
        tuple(c["id_champs"]) for c in tmp.get("to_skip", [])
    )

    print(f"Found {len(to_check)} comps to expand")
    for idx, db_comp in enumerate(to_check):
        comp = tuple(db_comp["id_champs"])
        champs = [ALL_CHAMPIONS[id].name for id in comp]
        print(f"[{idx} / {len(to_check)}] Expanding comp of size {len(comp)}: {champs}")

        update = find_comps(comp, to_skip)

        for new_comp in update:
            insert_comp(new_comp)

        db.execute(
            """
            UPDATE compositions
            SET is_expanded = 1
            WHERE id = ?
            """,
            [db_comp["id"]],
        )

        db.commit()


if __name__ == "__main__":
    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
