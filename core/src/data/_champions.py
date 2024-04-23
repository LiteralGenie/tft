from typing import ClassVar

# @todo: Move this to config file


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
    range: int
    traits: list[Trait]
    uses_ap: bool

    def __init__(
        self,
        cost: int,
        name: str,
        traits: list[Trait],
        range: int,
        uses_ap: bool,
    ):
        self.id = self._NEXT_ID
        self.__class__._NEXT_ID += 1

        self.cost = cost
        self.name = name
        self.traits = traits
        self.range = range
        self.uses_ap = uses_ap

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name


# fmt: off
_T = ALL_TRAITS
ALL_CHAMPIONS: list[Champion] = [
    # 1 costs
    Champion(1, "Ahri", [_T.FATED, _T.ARCANIST], 4, True),
    Champion(1, "Caitlyn", [_T.GHOSTLY, _T.SNIPER], 4, False),
    Champion(1, "Cho'Gath", [_T.MYTHIC, _T.BEHEMOTH], 1, True),
    Champion(1, "Darius", [_T.UMBRAL, _T.DUELIST], 1, True),

    Champion(1, "Kobuko", [_T.FORTUNE, _T.BRUISER], 1, True),
    Champion(1, "Garen", [_T.STORYWEAVER, _T.WARDEN], 1, False),
    Champion(1, "Jax", [_T.INKSHADOW, _T.WARDEN], 1, False),
    Champion(1, "Kha'Zix", [_T.HEAVENLY, _T.REAPER], 1, False),

    Champion(1, "Kog'Maw", [_T.MYTHIC, _T.INVOKER, _T.SNIPER], 4, False),
    Champion(1, "Malphite", [_T.HEAVENLY, _T.BEHEMOTH], 1, False),
    Champion(1, "Rek'Sai", [_T.DRYAD, _T.BRUISER], 1, False),
    Champion(1, "Sivir", [_T.STORYWEAVER, _T.TRICKSHOT], 4, False),

    Champion(1, "Yasuo", [_T.FATED, _T.DUELIST], 1, False),

    # 2 costs
    Champion(2, "Aatrox", [_T.GHOSTLY, _T.INKSHADOW, _T.BRUISER], 1, False),
    Champion(2, "Gnar", [_T.DRYAD, _T.WARDEN], 1, False),
    Champion(2, "Janna", [_T.DRAGONLORD, _T.INVOKER], 4, False),
    Champion(2, "Kindred", [_T.FATED, _T.DRYAD, _T.REAPER], 4, False),

    Champion(2, "Lux", [_T.PORCELAIN, _T.ARCANIST], 4, False),
    Champion(2, "Neeko", [_T.MYTHIC, _T.HEAVENLY, _T.ARCANIST], 1, False),
    Champion(2, "Qiyana", [_T.HEAVENLY, _T.DUELIST], 1, False),
    Champion(2, "Riven", [_T.STORYWEAVER, _T.ALTRUIST, _T.BRUISER], 1, False),

    Champion(2, "Senna", [_T.INKSHADOW, _T.SNIPER], 1, False),
    Champion(2, "Shen", [_T.GHOSTLY, _T.BEHEMOTH], 1, False),
    Champion(2, "Teemo", [_T.FORTUNE, _T.TRICKSHOT], 4, False),
    Champion(2, "Yorick", [_T.UMBRAL, _T.BEHEMOTH], 1, False),
    
    Champion(2, "Zyra", [_T.STORYWEAVER, _T.SAGE], 4, False),

    # 3 costs
    Champion(3, "Alune", [_T.UMBRAL, _T.INVOKER], 1, False),
    Champion(3, "Amumu", [_T.PORCELAIN, _T.WARDEN], 1, False),
    Champion(3, "Aphelios", [_T.FATED, _T.SNIPER], 4, False),
    Champion(3, "Bard", [_T.MYTHIC, _T.TRICKSHOT], 4, False),
    Champion(3, "Diana", [_T.DRAGONLORD, _T.SAGE], 1, False),
    Champion(3, "Illaoi", [_T.GHOSTLY, _T.ARCANIST, _T.WARDEN], 1, False),
    Champion(3, "Soraka", [_T.HEAVENLY, _T.ALTRUIST], 4, False),
    Champion(3, "Tahm Kench", [_T.MYTHIC, _T.BRUISER], 1, False),
    Champion(3, "Thresh", [_T.FATED, _T.BEHEMOTH], 2, False),
    Champion(3, "Tristana", [_T.FORTUNE, _T.DUELIST], 4, False),
    Champion(3, "Volibear", [_T.INKSHADOW, _T.DUELIST], 1, False),
    Champion(3, "Yone", [_T.UMBRAL, _T.REAPER], 1, False),
    Champion(3, "Zoe", [_T.FORTUNE, _T.STORYWEAVER, _T.ARCANIST], 4, False),

    # 4 costs
    Champion(4, "Annie", [_T.FORTUNE, _T.INVOKER], 1, False),
    Champion(4, "Ashe", [_T.PORCELAIN, _T.SNIPER], 4, False),
    Champion(4, "Galio", [_T.STORYWEAVER, _T.BRUISER], 1, False),
    Champion(4, "Kai'Sa", [_T.INKSHADOW, _T.TRICKSHOT], 4, False),

    Champion(4, "Kayn", [_T.GHOSTLY, _T.REAPER], 1, False),
    Champion(4, "Lee Sin", [_T.DRAGONLORD, _T.DUELIST], 1, False),
    Champion(4, "Lillia", [_T.MYTHIC, _T.INVOKER], 4, False),
    Champion(4, "Morganna", [_T.GHOSTLY, _T.SAGE], 4, False),

    Champion(4, "Nautilus", [_T.MYTHIC, _T.WARDEN], 1, False),
    Champion(4, "Ornn", [_T.DRYAD, _T.BEHEMOTH], 1, False),
    Champion(4, "Sylas", [_T.UMBRAL, _T.BRUISER], 1, False),
    Champion(4, "Syndra", [_T.FATED, _T.ARCANIST], 4, False),

    # 5 costs
    Champion(5, "Azir", [_T.DRYAD, _T.INVOKER], 4, False),
    Champion(5, "Hwei", [_T.MYTHIC], 4, False),
    Champion(5, "Irelia", [_T.STORYWEAVER, _T.DUELIST], 4, False),
    Champion(5, "Lissandra", [_T.PORCELAIN, _T.ARCANIST], 2, False),

    Champion(5, "Rakan", [_T.DRAGONLORD, _T.ALTRUIST], 4, False),
    Champion(5, "Sett", [_T.FATED, _T.UMBRAL, _T.WARDEN], 1, False),
    Champion(5, "Udyr", [_T.INKSHADOW, _T.BEHEMOTH], 1, False),
    Champion(5, "Wukong", [_T.HEAVENLY, _T.SAGE], 1, False),

    Champion(5, "Xayah", [_T.DRAGONLORD, _T.TRICKSHOT], 4, False),

]
# fmt: on

CHAMPIONS_BY_TRAIT: dict[Trait, set[Champion]] = dict()
for c in ALL_CHAMPIONS:
    for t in c.traits:
        CHAMPIONS_BY_TRAIT.setdefault(t, set())
        CHAMPIONS_BY_TRAIT[t].add(c)

CHAMPIONS_BY_ID: dict[int, Champion] = {c.id: c for c in ALL_CHAMPIONS}
