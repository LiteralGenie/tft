from functools import cached_property


class Composition:
    ids: list[int]

    def __init__(self, ids: list[int]) -> None:
        self.ids = ids

    @cached_property
    def hash(self) -> str:
        ids_sorted = sorted(self.ids)
        return ",".join(str(id) for id in ids_sorted)

    def __hash__(self) -> int:
        return hash(self.hash)

    def __eq__(self, value: object) -> bool:
        return hash(value) == hash(self)

    def add(self, id_champion: int):
        ids = self.ids.copy() + [id_champion]
        return Composition(ids)

    def __len__(self):
        return len(self.ids)
