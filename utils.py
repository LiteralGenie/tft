import pickle
import time
from pathlib import Path
from typing import TYPE_CHECKING

from data import CHAMPIONS_HASH

if TYPE_CHECKING:
    from count import Composition


def print_elapsed(start: float, *args, **kwargs):
    elapsed = time.time() - start
    print(f"[{elapsed:.1f}s]", *args, **kwargs)


FP_COMP = Path("./count.pkl")
MAX_TEAM_SIZE = 8


def load_comp_data() -> "list[Composition] | None":
    expected_hash = CHAMPIONS_HASH + "_" + str(MAX_TEAM_SIZE)

    FP_COMP = Path("./count.pkl")
    if FP_COMP.exists():
        with open(FP_COMP, "rb") as file:
            data = pickle.load(file)

            if data["hash"] == expected_hash:
                return data["comps"]


def dump_comp_data(comps: "set[Composition]"):
    expected_hash = CHAMPIONS_HASH + "_" + str(MAX_TEAM_SIZE)

    with open("count.pkl", "wb") as file:
        data = dict(
            hash=expected_hash,
            comps=comps,
        )
        pickle.dump(data, file)
