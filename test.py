from count import Composition
from data import CHAMPIONS


def test_hash_composition():
    assert hash(Composition(set([CHAMPIONS[0]]))) == hash(
        Composition(set([CHAMPIONS[0]]))
    )

    assert hash(Composition(set([CHAMPIONS[0]]))) != hash(
        Composition(set([CHAMPIONS[1]]))
    )


def test_hash_permutation():
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


def test_set_membership():
    s = set([CHAMPIONS[0]])
    assert CHAMPIONS[0] in s

    new_comp = lambda: Composition(set([CHAMPIONS[0]]))
    s = set([new_comp()])
    assert new_comp() in s


test_hash_composition()
test_hash_permutation()
test_set_membership()
