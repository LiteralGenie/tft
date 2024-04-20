from utils import load_comp_data

data = load_comp_data()
if not data:
    raise Exception


def print_size_score_table():
    score_counts = [0 for _ in range(20 + 1)]
    stats = [score_counts.copy() for _ in range(10 + 1)]

    for comp in data:
        stats[len(comp)][comp.score] += 1

    for by_size in stats:
        print(",\t".join(str(score) for score in by_size))
        print()


def print_by_score(score: int):
    filtered = [comp for comp in data if comp.score == score]
    for idx, comp in enumerate(filtered):
        print(idx, comp)

        traits = [(t, count) for (t, count) in comp.trait_counts.items()]
        traits.sort(key=lambda x: x[1], reverse=True)
        for t, count in traits:
            print("\t", str(count).rjust(2), t.name)


# print_size_score_table()
print_by_score(11)
