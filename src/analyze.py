from data._champions import ALL_TRAITS
from lib.composition import Composition
from lib.utils import load_comp_data

data = load_comp_data()
if not data:
    raise Exception


def score_by_tiers(comp: Composition, cap_heavenly=True):
    score = 0

    for trait, count in comp.trait_counts.items():
        for tier in trait.thresholds:
            if count >= tier:
                score += 1

                if cap_heavenly and trait is ALL_TRAITS.HEAVENLY:
                    break
            else:
                break

    return score


def print_size_score_table():
    score_counts = [0 for _ in range(20 + 1)]
    stats = [score_counts.copy() for _ in range(10 + 1)]

    for comp in data:
        stats[len(comp)][score_by_tiers(comp)] += 1

    for by_size in stats:
        print(", ".join(str(score) for score in by_size))


def print_by_size_score(size: int, min_score: int):
    filtered = [
        comp
        for comp in data
        if (score_by_tiers(comp) >= min_score and len(comp) == size)
    ]
    for idx, comp in enumerate(filtered):
        print(size, score_by_tiers(comp), idx, comp)

        traits = [(t, count) for (t, count) in comp.trait_counts.items()]
        traits.sort(key=lambda x: x[1], reverse=True)
        for t, count in traits:
            print("\t", str(count).rjust(2), t.name)


# print_size_score_table()
print_by_size_score(6, 6)
