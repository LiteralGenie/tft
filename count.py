import time
from functools import cached_property

from data import CHAMPIONS, CHAMPIONS_BY_TRAIT, Champion
from utils import print_elapsed


class Composition:
    champions: list[Champion]

    def __init__(self, champions: list[Champion]):
        self.champions = champions

    @cached_property
    def hash(self) -> int:
        ids = [c.id for c in self.champions]
        ids.sort()
        return hash(tuple(ids))

    def __eq__(self, other: object) -> bool:
        return hash(other) == hash(self)

    def __hash__(self) -> int:
        return self.hash

    def __len__(self):
        return len(self.champions)

    def __repr__(self) -> str:
        cs = ", ".join([c.__repr__() for c in self.champions])
        return f"({cs})"

    def add(self, champion: Champion) -> "Composition":
        result = [*self.champions.copy(), champion]
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


def expand_comp(comp: Composition) -> list[Composition]:
    traits = set(t for c in comp.champions for t in c.traits)

    candidates: set[Champion] = set()
    for t in traits:
        for c in CHAMPIONS_BY_TRAIT[t]:
            if c not in comp.champions:
                candidates.add(c)

    return [comp.add(c) for c in candidates]


cache_hits = 0


def find_champion_comps(champion: Champion, skip: set[Composition]) -> set[Composition]:
    # Skip gets mutated for efficiency

    global cache_hits

    print(champion.name)

    init = Composition([champion])
    comps: dict[int, Composition] = dict()
    prev: dict[int, Composition] = {hash(init): init}

    start = time.time()
    for size in range(7):
        update: dict[int, Composition] = dict()

        for comp in prev.values():
            if comp in skip:
                cache_hits += 1
                continue

            skip.add(comp)

            expansions = expand_comp(comp)

            for expanded in expansions:
                update[hash(expanded)] = expanded
                comps[hash(expanded)] = expanded

        prev = update
        print_elapsed(
            start,
            f"Calculated {len(update)} comps of size {size+2} with {cache_hits} cache_hits",
        )

    return comps


def main():
    comps: set[Composition] = set()

    start = time.time()
    for champion in CHAMPIONS:
        find_champion_comps(champion, comps)
    print_elapsed(start, f"Found {len(comps):,} compositions")

    for size in range(1, 11):
        filtered = [c for c in comps if len(c) == size]
        print(f"{len(filtered):,} comps of size {size}")

    for score in range(20):
        filtered = [c for c in comps if c.score == score]
        print(f"{len(filtered):,} comps with score {score}")


if __name__ == "__main__":
    import cProfile
    from pstats import SortKey

    cProfile.run("main()", sort=SortKey.CUMULATIVE)

    # main()
