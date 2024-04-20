import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from data import CHAMPIONS_HASH

if TYPE_CHECKING:
    from count import Composition


def print_elapsed(start: float, *args, **kwargs):
    elapsed = time.time() - start
    print(f"[{elapsed:.1f}s]", *args, **kwargs)


FP_COMP = Path("./count.json")
MAX_TEAM_SIZE = 8


def load_comp_data() -> "list[Composition] | None":
    from count import Composition

    expected_hash = CHAMPIONS_HASH + "_" + str(MAX_TEAM_SIZE)

    if FP_COMP.exists():
        with open(FP_COMP) as file:
            data = json.load(file)

            if data["hash"] == expected_hash:
                return [Composition.load(ln) for ln in data["lines"]]
            else:
                print("Cache exists but invalid (or outdated) hash")
                answer = input("(y/n) Override? ")
                if answer.strip().lower() != "y":
                    sys.exit()


def dump_comp_data(comps: "set[Composition]"):
    expected_hash = CHAMPIONS_HASH + "_" + str(MAX_TEAM_SIZE)

    with open(FP_COMP, "w") as file:
        lines = [comp.dump() for comp in comps]

        data = dict(
            hash=expected_hash,
            lines=lines,
        )
        json.dump(data, file, indent=2)
