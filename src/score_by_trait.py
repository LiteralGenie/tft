from tqdm import tqdm

from lib.composition import Composition
from lib.db import (
    DbTrait,
    get_all_champions,
    get_all_traits,
    get_champions_by_trait,
    init_db,
)

db = init_db()
ALL_CHAMPIONS = get_all_champions(db)
ALL_TRAITS = get_all_traits(db)

TRAIT_WEIGHTS: dict[DbTrait, list[float]] = dict()


def init_trait_weights():
    def find_trait(name: str):
        for trait in ALL_TRAITS.values():
            if trait.name == name:
                return trait
        else:
            raise Exception(f'Trait not found: "{name}"')

    def assign_weight(trait: DbTrait, weights: list[float]):
        global TRAIT_WEIGHTS

        assert trait not in TRAIT_WEIGHTS
        assert len(weights) == len(trait.thresholds)

        TRAIT_WEIGHTS[trait] = weights

    trait = find_trait("Heavenly")
    weights: list[float] = [0, 1, 0, 1, 0, 1]
    # assuming thresholds:  2  3  4  5  6  7
    assign_weight(trait, weights)


def find_missing_scores() -> list[int]:
    rows = db.execute(
        """
        SELECT c.id
        FROM compositions c
        LEFT JOIN scores_by_trait s
        ON s.id_composition = c.id
        WHERE s.id_composition IS NULL 
        """
    ).fetchall()

    return [r["id"] for r in rows]


def fetch_comp(id: int) -> Composition:
    rows = db.execute(
        """
        SELECT id_champion
        FROM composition_champions
        WHERE id_composition = ?
        """,
        [id],
    ).fetchall()

    return Composition([r["id_champion"] for r in rows])


def count_traits(comp: Composition) -> dict[DbTrait, int]:
    champs = [ALL_CHAMPIONS[id] for id in comp.ids]

    counts: dict[int, int] = dict()
    for c in champs:
        for id in c.traits:
            counts.setdefault(id, 0)
            counts[id] += 1

    return {ALL_TRAITS[id]: count for id, count in counts.items()}


def calc_score(comp: Composition) -> float:
    score = 0

    trait_counts = count_traits(comp)
    for trait, count in trait_counts.items():
        for idx, thresh in enumerate(trait.thresholds):
            weight_overrides = TRAIT_WEIGHTS.get(trait)

            if count >= thresh:
                if not weight_overrides:
                    # No weight override, use default
                    score += 1
                elif idx < len(weight_overrides):
                    # Use weight override
                    score += weight_overrides[idx]
                else:
                    # Weight overrides exist but this trait count exceeds highest threshold
                    score += 0
            else:
                # Thresholds are in ascending order so we stop checking when one is smaller
                break

    return score


def insert_score(id_composition: int, score: float):
    db.execute(
        """
        INSERT OR REPLACE INTO scores_by_trait
            (id_composition, score) VALUES
            (?, ?)
        """,
        [id_composition, score],
    )


if __name__ == "__main__":
    missing = find_missing_scores()

    for idx, id in enumerate(tqdm(missing)):
        comp = fetch_comp(id)
        score = calc_score(comp)
        insert_score(id, score)

        if idx % 100_000 == 0:
            db.commit()
