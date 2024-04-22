from typing import ClassVar


class Trait:
    _NEXT_ID: ClassVar[int] = 0

    id: int
    name: str
    thresholds: list[int]

    def __init__(self, name: str, tiers: list[int]):
        self.id = self._NEXT_ID
        self.__class__._NEXT_ID += 1

        self.name = name
        self.thresholds = tiers

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name


class ALL_TRAITS:
    ALTRUIST = Trait("Altruist", [2, 3, 4])
    ARCANIST = Trait("Arcanist", [2, 4, 6, 8])
    BEHEMOTH = Trait("Behemoth", [2, 4, 6])
    BRUISER = Trait("Bruiser", [2, 4, 6, 8])

    DRAGONLORD = Trait("Dragonlord", [2, 3, 4, 5])
    DRYAD = Trait("Dryad", [2, 4, 6])
    DUELIST = Trait("Duelist", [2, 4, 6, 8])
    FATED = Trait("Fated", [3, 5, 7, 10])

    FORTUNE = Trait("Fortune", [3, 5])
    GHOSTLY = Trait("Ghostly", [2, 4, 6, 8])
    HEAVENLY = Trait("Heavenly", [2, 3, 4, 5, 6, 7])
    INKSHADOW = Trait("Inkshadow", [3, 5, 7])

    INVOKER = Trait("Invoker", [2, 4, 6])
    MYTHIC = Trait("Mythic", [3, 5, 7, 10])
    PORCELAIN = Trait("Porcelain", [2, 4, 6])
    STORYWEAVER = Trait("Storyweaver", [3, 5, 7, 10])

    REAPER = Trait("Reaper", [2, 4])
    SAGE = Trait("Sage", [2, 3, 4, 5])
    SNIPER = Trait("Sniper", [2, 4, 6])
    TRICKSHOT = Trait("Trickshot", [2, 4])

    UMBRAL = Trait("Umbral", [2, 4, 6, 9])
    WARDEN = Trait("Warden", [2, 4, 6])


class Champion:
    _NEXT_ID: ClassVar[int] = 0

    id: int
    cost: int
    name: str
    traits: list[Trait]

    def __init__(self, cost: int, name: str, traits: list[Trait]):
        self.id = self._NEXT_ID
        self.__class__._NEXT_ID += 1

        self.cost = cost
        self.name = name
        self.traits = traits

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name


# fmt: off
_T = ALL_TRAITS
ALL_CHAMPIONS: list[Champion] = [
    # 1 costs
    Champion(1, "Ahri", [_T.FATED, _T.ARCANIST]),
    Champion(1, "Caitlyn", [_T.GHOSTLY, _T.SNIPER]),
    Champion(1, "Cho'Gath", [_T.MYTHIC, _T.BEHEMOTH]),
    Champion(1, "Darius", [_T.UMBRAL, _T.DUELIST]),

    Champion(1, "Kobuko", [_T.FORTUNE, _T.BRUISER]),
    Champion(1, "Garen", [_T.STORYWEAVER, _T.WARDEN]),
    Champion(1, "Jax", [_T.INKSHADOW, _T.WARDEN]),
    Champion(1, "Kha'Zix", [_T.HEAVENLY, _T.REAPER]),

    Champion(1, "Kog'Maw", [_T.MYTHIC, _T.INVOKER, _T.SNIPER]),
    Champion(1, "Malphite", [_T.HEAVENLY, _T.BEHEMOTH]),
    Champion(1, "Rek'Sai", [_T.DRYAD, _T.BRUISER]),
    Champion(1, "Sivir", [_T.STORYWEAVER, _T.TRICKSHOT]),

    Champion(1, "Yasuo", [_T.FATED, _T.DUELIST]),

    # 2 costs
    Champion(2, "Aatrox", [_T.GHOSTLY, _T.INKSHADOW, _T.BRUISER]),
    Champion(2, "Gnar", [_T.DRYAD, _T.WARDEN]),
    Champion(2, "Janna", [_T.DRAGONLORD, _T.INVOKER]),
    Champion(2, "Kindred", [_T.FATED, _T.DRYAD, _T.REAPER]),

    Champion(2, "Lux", [_T.PORCELAIN, _T.ARCANIST]),
    Champion(2, "Neeko", [_T.MYTHIC, _T.HEAVENLY, _T.ARCANIST]),
    Champion(2, "Qiyana", [_T.HEAVENLY, _T.DUELIST]),
    Champion(2, "Riven", [_T.STORYWEAVER, _T.ALTRUIST, _T.BRUISER]),

    Champion(2, "Senna", [_T.INKSHADOW, _T.SNIPER]),
    Champion(2, "Shen", [_T.GHOSTLY, _T.BEHEMOTH]),
    Champion(2, "Teemo", [_T.FORTUNE, _T.TRICKSHOT]),
    Champion(2, "Yorick", [_T.UMBRAL, _T.BEHEMOTH]),
    
    Champion(2, "Zyra", [_T.STORYWEAVER, _T.SAGE]),

    # 3 costs
    Champion(3, "Alune", [_T.UMBRAL, _T.INVOKER]),
    Champion(3, "Amumu", [_T.PORCELAIN, _T.WARDEN]),
    Champion(3, "Aphelios", [_T.FATED, _T.SNIPER]),
    Champion(3, "Bard", [_T.MYTHIC, _T.TRICKSHOT]),
    Champion(3, "Diana", [_T.DRAGONLORD, _T.SAGE]),
    Champion(3, "Illaoi", [_T.GHOSTLY, _T.ARCANIST, _T.WARDEN]),
    Champion(3, "Soraka", [_T.HEAVENLY, _T.ALTRUIST]),
    Champion(3, "Tahm Kench", [_T.MYTHIC, _T.BRUISER]),
    Champion(3, "Thresh", [_T.FATED, _T.BEHEMOTH]),
    Champion(3, "Tristana", [_T.FORTUNE, _T.DUELIST]),
    Champion(3, "Volibear", [_T.INKSHADOW, _T.DUELIST]),
    Champion(3, "Yone", [_T.UMBRAL, _T.REAPER]),
    Champion(3, "Zoe", [_T.FORTUNE, _T.STORYWEAVER, _T.ARCANIST]),

    # 4 costs
    Champion(4, "Annie", [_T.FORTUNE, _T.INVOKER]),
    Champion(4, "Ashe", [_T.PORCELAIN, _T.SNIPER]),
    Champion(4, "Galio", [_T.STORYWEAVER, _T.BRUISER]),
    Champion(4, "Kai'Sa", [_T.INKSHADOW, _T.TRICKSHOT]),

    Champion(4, "Kayn", [_T.GHOSTLY, _T.REAPER]),
    Champion(4, "Lee Sin", [_T.DRAGONLORD, _T.DUELIST]),
    Champion(4, "Lillia", [_T.MYTHIC, _T.INVOKER]),
    Champion(4, "Morganna", [_T.GHOSTLY, _T.SAGE]),

    Champion(4, "Nautilus", [_T.MYTHIC, _T.WARDEN]),
    Champion(4, "Ornn", [_T.DRYAD, _T.BEHEMOTH]),
    Champion(4, "Sylas", [_T.UMBRAL, _T.BRUISER]),
    Champion(4, "Syndra", [_T.FATED, _T.ARCANIST]),

]
# fmt: on

CHAMPIONS_BY_TRAIT: dict[Trait, set[Champion]] = dict()
for c in ALL_CHAMPIONS:
    for t in c.traits:
        CHAMPIONS_BY_TRAIT.setdefault(t, set())
        CHAMPIONS_BY_TRAIT[t].add(c)

CHAMPIONS_BY_ID: dict[int, Champion] = {c.id: c for c in ALL_CHAMPIONS}
