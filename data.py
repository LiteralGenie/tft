from dataclasses import dataclass
from typing import ClassVar


class Trait:
    _NEXT_ID: ClassVar[int] = 0

    id: int
    name: str

    def __init__(self, name: str):
        self.id = self._NEXT_ID
        self.__class__._NEXT_ID += 1

        self.name = name

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name


class TRAITS:
    ALTRUIST = Trait("Altruist")
    ARCANIST = Trait("Arcanist")
    BEHEMOTH = Trait("Behemoth")
    BRUISER = Trait("Bruiser")

    DRAGONLORD = Trait("Dragonlord")
    DRYAD = Trait("Dryad")
    DUELIST = Trait("Duelist")
    FATED = Trait("Fated")

    FORTUNE = Trait("Fortune")
    GHOSTLY = Trait("Ghostly")
    HEAVENLY = Trait("Heavenly")
    INKSHADOW = Trait("Inkshadow")

    INVOKER = Trait("Invoker")
    MYTHIC = Trait("Mythic")
    PORCELAIN = Trait("Porcelain")
    STORYWEAVER = Trait("Storyweaver")

    REAPER = Trait("Reaper")
    SAGE = Trait("Sage")
    SNIPER = Trait("Sniper")
    TRICKSHOT = Trait("Trickshot")

    UMBRAL = Trait("Umbral")
    WARDEN = Trait("Warden")


class Champion:
    _NEXT_ID: ClassVar[int] = 0

    id: int
    name: str
    traits: list[Trait]

    def __init__(self, name: str, traits: list[Trait]):
        self.id = self._NEXT_ID
        self.__class__._NEXT_ID += 1

        self.name = name
        self.traits = traits

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return self.name


# fmt: off
_T = TRAITS
CHAMPIONS: list[Champion] = [
    # 1 costs
    Champion("Ahri", [_T.FATED, _T.ARCANIST]),
    Champion("Caitlyn", [_T.GHOSTLY, _T.SNIPER]),
    Champion("Cho'Gath", [_T.MYTHIC, _T.BEHEMOTH]),
    Champion("Darius", [_T.UMBRAL, _T.DUELIST]),

    Champion("Kobuko", [_T.FORTUNE, _T.BRUISER]),
    Champion("Garen", [_T.STORYWEAVER, _T.WARDEN]),
    Champion("Jax", [_T.INKSHADOW, _T.WARDEN]),
    Champion("Kha'Zix", [_T.HEAVENLY, _T.REAPER]),

    Champion("Kog'Maw", [_T.MYTHIC, _T.INVOKER, _T.SNIPER]),
    Champion("Malphite", [_T.HEAVENLY, _T.BEHEMOTH]),
    Champion("Rek'Sai", [_T.FATED, _T.ARCANIST]),
    Champion("Sivir", [_T.STORYWEAVER, _T.TRICKSHOT]),

    Champion("Yasuo", [_T.FATED, _T.DUELIST]),

    # 2 costs
    Champion("Aatrox", [_T.GHOSTLY, _T.INKSHADOW, _T.BRUISER]),
    Champion("Gnar", [_T.DRYAD, _T.WARDEN]),
    Champion("Janna", [_T.DRAGONLORD, _T.INVOKER]),
    Champion("Kindred", [_T.FATED, _T.DRYAD, _T.REAPER]),

    Champion("Lux", [_T.PORCELAIN, _T.ARCANIST]),
    Champion("Neeko", [_T.MYTHIC, _T.HEAVENLY, _T.ARCANIST]),
    Champion("Qiyana", [_T.HEAVENLY, _T.DUELIST]),
    Champion("Riven", [_T.STORYWEAVER, _T.ALTRUIST, _T.BRUISER]),

    Champion("Senna", [_T.INKSHADOW, _T.SNIPER]),
    Champion("Shen", [_T.GHOSTLY, _T.BEHEMOTH]),
    Champion("Teemo", [_T.FORTUNE, _T.TRICKSHOT]),
    Champion("Yorick", [_T.UMBRAL, _T.BEHEMOTH]),
    
    Champion("Zyra", [_T.STORYWEAVER, _T.SAGE]),

    # 3 costs
    Champion("Alune", [_T.UMBRAL, _T.INVOKER]),
    Champion("Amumu", [_T.PORCELAIN, _T.WARDEN]),
    Champion("Aphelios", [_T.FATED, _T.SNIPER]),
    Champion("Bard", [_T.MYTHIC, _T.TRICKSHOT]),
    Champion("Diana", [_T.DRAGONLORD, _T.SAGE]),
    Champion("Illaoi", [_T.GHOSTLY, _T.ARCANIST, _T.WARDEN]),
    Champion("Soraka", [_T.HEAVENLY, _T.ALTRUIST]),
    Champion("Tahm Kench", [_T.MYTHIC, _T.BRUISER]),
    Champion("Thresh", [_T.FATED, _T.BEHEMOTH]),
    Champion("Tristana", [_T.FORTUNE, _T.DUELIST]),
    Champion("Volibear", [_T.INKSHADOW, _T.DUELIST]),
    Champion("Yone", [_T.UMBRAL, _T.REAPER]),
    Champion("Zoe", [_T.FORTUNE, _T.STORYWEAVER, _T.ARCANIST]),
]
# fmt: on

CHAMPIONS_BY_TRAIT: dict[Trait, set[Champion]] = dict()
for c in CHAMPIONS:
    for t in c.traits:
        CHAMPIONS_BY_TRAIT.setdefault(t, set())
        CHAMPIONS_BY_TRAIT[t].add(c)
