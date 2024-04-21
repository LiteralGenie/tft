import time
from functools import cached_property
from itertools import chain

from data import CHAMPIONS, CHAMPIONS_BY_ID, CHAMPIONS_BY_TRAIT, Champion, Trait
from utils import MAX_TEAM_SIZE, dump_comp_data, load_comp_data, print_elapsed


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
        result = list(chain(self.champions, [champion]))
        return Composition(result)

    @cached_property
    def trait_counts(self):
        trait_counts: dict[Trait, int] = dict()

        for c in self.champions:
            for t in c.traits:
                trait_counts.setdefault(t, 0)
                trait_counts[t] += 1

        return trait_counts

    def dump(self) -> list[int]:
        return [c.id for c in self.champions]

    @classmethod
    def load(cls, data: list[int]) -> "Composition":
        cs = [CHAMPIONS_BY_ID[id] for id in data]
        return cls(cs)


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
    comps: dict[int, Composition] = {hash(init): init}
    prev: dict[int, Composition] = {hash(init): init}

    start = time.time()
    for size in range(2, MAX_TEAM_SIZE + 1):
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
            f"Calculated {len(update)} comps of size {size} with {cache_hits} cache_hits",
        )

    return comps


def main():
    comps: set[Composition] = load_comp_data()
    if not comps:
        answer = input("(y/n) Override? ")
        if answer.strip().lower() != "y":
            return

        start = time.time()

        comps = set()
        seen = set()
        for champion in CHAMPIONS:
            update = find_champion_comps(champion, seen)
            comps.update(update.values())

        dump_comp_data(comps)

        print_elapsed(start, f"Found {len(comps):,} compositions")

    for size in range(1, 11):
        filtered = [c for c in comps if len(c) == size]
        print(f"{len(filtered):,} comps of size {size}")


if __name__ == "__main__":
    # import cProfile
    # from pstats import SortKey

    # cProfile.run("main()", sort=SortKey.CUMULATIVE)

    main()
