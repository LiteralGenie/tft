import time
from functools import cached_property

from data import CHAMPIONS, CHAMPIONS_BY_TRAIT, Champion
from utils import print_elapsed


class Composition:
    champions: set[Champion]

    def __init__(self, champions: set[Champion]):
        self.champions = champions

    @cached_property
    def hash(self) -> int:
        ids = [c.id for c in self.champions]
        ids.sort()
        return hash(tuple(ids))

    def __hash__(self) -> int:
        return self.hash

    def __len__(self):
        return len(self.champions)

    def __repr__(self) -> str:
        cs = ", ".join([c.__repr__() for c in self.champions])
        return f"({cs})"

    def add(self, champion: Champion) -> "Composition":
        result = self.champions.copy()
        result.add(champion)
        return Composition(result)

    @cached_property
    def score(self):
        trait_counts: dict[int, int] = dict()

        for c in self.champions:
            for t in c.traits:
                trait_counts.setdefault(t.id, 0)
                trait_counts[t.id] += 1

        vs = list(trait_counts.values())
        total = sum(vs) - len(vs)
        return total


def expand_comp(comp: Composition) -> set[Composition]:
    traits = set(t for c in comp.champions for t in c.traits)

    candidates: set[Champion] = set()
    for t in traits:
        for c in CHAMPIONS_BY_TRAIT[t]:
            if c not in comp.champions:
                candidates.add(c)

    return set([comp.add(c) for c in candidates])


cache_hits = 0


def find_champion_comps(
    champion: Champion, skip: set[Composition] | None = None
) -> set[Composition]:
    # Skip gets mutated for efficiency
    skip = skip or set()

    init = Composition(set([champion]))
    comps: set[Composition] = set([init])
    prev: set[Composition] = set([init])

    start = time.time()
    for _ in range(5):
        update: set[Composition] = set()

        for comp in prev:
            if comp in skip:
                cache_hits += 1
                continue

            skip.add(comp)

            expansions = expand_comp(comp)
            update.update(expansions)

        comps.update(update)
        prev = update
        print_elapsed(start, f"Expanded to {len(update)} comps")

    return comps


assert hash(
    Composition(
        set(
            [
                CHAMPIONS[0],
                CHAMPIONS[1],
            ]
        )
    )
) == hash(
    Composition(
        set(
            [
                CHAMPIONS[1],
                CHAMPIONS[0],
            ]
        )
    )
)


def main():
    start = time.time()
    find_champion_comps(CHAMPIONS[0])
    print_elapsed(start, "done")


if __name__ == "__main__":
    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
