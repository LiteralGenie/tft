from functools import cached_property

from tqdm import tqdm

from lib.db import (
    DbChampion,
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)

MAX_TEAM_SIZE = 8

db = init_db()
ALL_CHAMPIONS = get_all_champions(db)
ALL_TRAITS = get_all_traits(db)
CHAMPIONS_BY_TRAIT = get_champions_by_trait(ALL_CHAMPIONS.values())


class Composition:
    ids: list[int]

    def __init__(self, ids: list[int]) -> None:
        self.ids = ids

    @cached_property
    def hash(self) -> str:
        ids_sorted = sorted(self.ids)
        return ",".join(str(id) for id in ids_sorted)

    def __hash__(self) -> int:
        return hash(self.hash)

    def add(self, id_champion: int):
        ids = self.ids.copy() + [id_champion]
        return Composition(ids)

    def __len__(self):
        return len(self.ids)


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
        WHERE hash = ?
        """,
        [comp.hash],
    ).fetchone()

    return result != None


def insert_comp(comp: Composition):
    id_comp = db.execute(
        """
        INSERT INTO compositions
            (hash) VALUES (?)
        RETURNING id;
        """,
        [comp.hash],
    ).fetchone()["id"]

    db.executemany(
        """
        INSERT INTO composition_champions
            (id_composition, id_champion) VALUES
            (?, ?)
        """,
        [(id_comp, id_champ) for id_champ in comp.ids],
    )


def find_comps_to_expand():
    rows = db.execute(
        """
        SELECT
            id,
            GROUP_CONCAT(champ.id_champion) id_champs
        FROM compositions comp
        INNER JOIN composition_champions champ
            ON comp.id = champ.id_composition
        WHERE comp.is_expanded = 0
        GROUP BY comp.id
        """
    ).fetchall()

    comps = [dict(r) for r in rows]
    for new_comp in comps:
        new_comp["comp"] = Composition(
            [int(id) for id in new_comp["id_champs"].split(",")]
        )

    return comps


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
            insert_comp(Composition([champ.id]))
            db.commit()

    while True:
        comps = find_comps_to_expand()
        comps = [x for x in comps if len(x["comp"]) < MAX_TEAM_SIZE]

        if not comps:
            break

        for idx, db_comp in enumerate(tqdm(comps)):
            cmp = db_comp["comp"]

            update = expand_comp(cmp)
            update = [cmp for cmp in update if not check_exists(cmp)]

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

            # This loop runs at ~2500 its / sec as long as
            # this commit() isn't called too frequently
            if idx % 10_000 == 0:
                db.commit()

        db.commit()


if __name__ == "__main__":
    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
