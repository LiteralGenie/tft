import multiprocessing
import time
from dataclasses import dataclass
from itertools import chain
from typing import Iterable, TypeAlias

from lib.composition import Composition
from lib.db import DbTrait, get_all_champions, get_all_traits, init_db
from lib.utils import print_elapsed, to_n_batches
from psycopg import Cursor
from tqdm import tqdm

db = init_db()
cursor = db.cursor()
ALL_CHAMPIONS = get_all_champions(db)
ALL_TRAITS = get_all_traits(db)

TraitWeights: TypeAlias = dict[DbTrait, list[float]]
TRAIT_WEIGHTS: TraitWeights = dict()

N_WORKERS = 8
POOL: multiprocessing.Pool = None


@dataclass
class CompositionScore:
    id_composition: str
    score: float


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
    weights: list[float] = [1, 0, 1, 0, 1, 0]
    # assuming thresholds:  2  3  4  5  6  7
    assign_weight(trait, weights)


def find_missing_scores(limit: int) -> list[str]:
    # Limit h
    rows = db.execute(
        """
        SELECT c.id
        FROM compositions c
        LEFT JOIN scores_by_trait s
            ON s.id_composition = c.id
        WHERE
            s.id_composition IS NULL
        LIMIT %s 
        """,
        [limit],
    ).fetchall()

    return [r["id"] for r in rows]


def _get_comps(hashes: list[str]) -> list[Composition]:
    comps: list[Composition] = []
    for h in hashes:
        champ_ids = [int(id) for id in h.split(",")]
        comps.append(Composition(champ_ids))

    return comps


def get_comps(hashes: list[str]) -> list[Composition]:
    batches = to_n_batches(hashes, N_WORKERS)

    results = list(POOL.imap_unordered(_get_comps, batches))

    return list(chain(*results))


def count_traits(comp: Composition) -> dict[DbTrait, int]:
    champs = [ALL_CHAMPIONS[id] for id in comp.ids]

    counts: dict[int, int] = dict()
    for c in champs:
        for id in c.traits:
            counts.setdefault(id, 0)
            counts[id] += 1

    return {ALL_TRAITS[id]: count for id, count in counts.items()}


def calc_score(comp: Composition, weights: TraitWeights) -> CompositionScore:
    score = 0

    trait_counts = count_traits(comp)
    for trait, count in trait_counts.items():
        overrides = weights.get(trait)

        for idx, thresh in enumerate(trait.thresholds):
            if count >= thresh:
                if not overrides:
                    # No weight override, use default
                    score += 1
                elif idx < len(overrides):
                    # Use weight override
                    score += overrides[idx]
                else:
                    # Weight overrides for trait but not this count (which is larger than max threshold)
                    break
            else:
                # Thresholds are in ascending order so we stop checking when one is smaller
                break

    return CompositionScore(
        id_composition=comp.hash,
        score=score,
    )


def _calc_scores(
    comps: list[Composition], weights: TraitWeights
) -> list[CompositionScore]:
    return [calc_score(c, weights) for c in comps]


def calc_scores(
    comps: list[Composition], weights: TraitWeights
) -> list[CompositionScore]:
    batches = to_n_batches(comps, N_WORKERS)
    args = [(b, weights) for b in batches]

    results = list(POOL.starmap(_calc_scores, args))

    return list(chain(*results))


def insert_scores(cursor: Cursor, scores: Iterable[CompositionScore]):
    params = [(s.id_composition, s.score) for s in scores]
    with cursor.copy("COPY scores_by_trait (id_composition, score) FROM STDIN") as copy:
        for p in params:
            copy.write_row(p)


if __name__ == "__main__":
    POOL = multiprocessing.Pool(N_WORKERS)

    init_trait_weights()

    while True:
        start = time.time()

        print_elapsed(start, "fetching comps to score")
        missing = find_missing_scores(limit=1_000_000)
        if not missing:
            print_elapsed(start, "all comps scored")
            break

        print_elapsed(start, "building comps")
        comps = get_comps(missing)

        print_elapsed(start, "calculating scores")
        scores = calc_scores(comps, TRAIT_WEIGHTS)

        print_elapsed(start, "inserting scores")
        with db.transaction():
            insert_scores(cursor, scores)

        print_elapsed(start, "done")

    db.commit()
