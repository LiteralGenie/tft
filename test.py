from count import Composition
from data import ALL_CHAMPIONS


def test_hash_composition():
    assert hash(Composition(set([ALL_CHAMPIONS[0]]))) == hash(
        Composition(set([ALL_CHAMPIONS[0]]))
    )

    assert hash(Composition(set([ALL_CHAMPIONS[0]]))) != hash(
        Composition(set([ALL_CHAMPIONS[1]]))
    )


def test_hash_permutation():
    assert hash(
        Composition(
            set(
                [
                    ALL_CHAMPIONS[0],
                    ALL_CHAMPIONS[1],
                ]
            )
        )
    ) == hash(
        Composition(
            set(
                [
                    ALL_CHAMPIONS[1],
                    ALL_CHAMPIONS[0],
                ]
            )
        )
    )


def test_set_membership():
    s = set([ALL_CHAMPIONS[0]])
    assert ALL_CHAMPIONS[0] in s

    new_comp = lambda: Composition(set([ALL_CHAMPIONS[0]]))
    s = set([new_comp()])
    assert new_comp() in s


test_hash_composition()
test_hash_permutation()
test_set_membership()
