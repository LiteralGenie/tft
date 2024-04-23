import sqlite3
from dataclasses import dataclass
from typing import Iterable, TypeAlias, cast

from data._champions import ALL_CHAMPIONS, ALL_TRAITS, Trait
from lib.config import DB_FILE

Database: TypeAlias = sqlite3.Connection


def init_db() -> Database:
    db = sqlite3.connect(DB_FILE)

    db.row_factory = sqlite3.Row

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS champions (
            id          INTEGER     PRIMARY KEY,

            cost        INTEGER     NOT NULL,
            name        TEXT        NOT NULL,
            range       INTEGER     NOT NULL,
            uses_ap     BOOLEAN     NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS traits (
            id      INTEGER     PRIMARY KEY,

            name    TEXT        NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS trait_thresholds (
            id          INTEGER     PRIMARY KEY,
            id_trait    INTEGER     NOT NULL,

            threshold   INTEGER     NOT NULL,

            FOREIGN KEY (id_trait) REFERENCES traits(id),

            UNIQUE (id_trait, threshold)
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS champion_traits (
            id_champion     INTEGER     NOT NULL,
            id_trait        INTEGER     NOT NULL,

            FOREIGN KEY (id_champion) REFERENCES champions(id),
            FOREIGN KEY (id_trait) REFERENCES traits(id),
            PRIMARY KEY (id_champion, id_trait)
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS compositions (
            id              INTEGER     PRIMARY KEY,

            hash            TEXT        NOT NULL,
            is_expanded     BOOLEAN     NOT NULL    DEFAULT 0,
            size            INTEGER     NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS composition_champions (
            id_composition      INTEGER     NOT NULL,
            id_champion         INTEGER     NOT NULL,

            FOREIGN KEY (id_composition) REFERENCES compositions(id),
            FOREIGN KEY (id_champion) REFERENCES champions(id),
            PRIMARY KEY (id_champion, id_composition),

            UNIQUE (id_composition, id_champion)
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS scores_by_trait (
            id_composition  INTEGER     PRIMARY KEY,

            score           REAL        NOT NULL,

            FOREIGN KEY (id_composition) REFERENCES compositions(id)
        )
        """
    )

    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS hash ON compositions (hash);
        """
    )

    _init_data(db)

    db.commit()

    return db


def _init_data(db: Database):
    trait_rows = db.execute("""SELECT COUNT(*) count FROM traits""").fetchone()["count"]
    if trait_rows == 0:
        for key, trait in ALL_TRAITS.__dict__.items():
            if key.startswith("__"):
                continue

            trait = cast(Trait, trait)

            db.execute(
                """
                    INSERT INTO traits 
                        (id, name) VALUES
                        (?, ?)
                """,
                [trait.id, trait.name],
            )

            for thresh in trait.thresholds:
                db.execute(
                    """
                        INSERT INTO trait_thresholds
                            (id_trait, threshold) VALUES
                            (?, ?)
                    """,
                    [trait.id, thresh],
                )

    champ_rows = db.execute("""SELECT COUNT(*) count FROM champions""").fetchone()[
        "count"
    ]
    if champ_rows == 0:
        for ch in ALL_CHAMPIONS:
            db.execute(
                """
                INSERT INTO CHAMPIONS
                    (id, cost, name, range, uses_ap) VALUES
                    (?, ?, ?, ?, ?)
                """,
                [ch.id, ch.cost, ch.name, ch.range, ch.uses_ap],
            )

            for trait in ch.traits:
                db.execute(
                    """
                    INSERT INTO champion_traits
                        (id_champion, id_trait) VALUES
                        (?, ?)
                    """,
                    [ch.id, trait.id],
                )


@dataclass
class DbTrait:
    id: int
    name: str
    thresholds: list[int]

    def __hash__(self) -> int:
        return self.id


def get_all_traits(db: Database) -> dict[int, DbTrait]:
    rows = db.execute(
        """
        SELECT t.id, t.name, GROUP_CONCAT(thresh.threshold) thresholds FROM traits t
        LEFT JOIN trait_thresholds thresh
        ON thresh.id_trait = t.id
        GROUP BY t.id
        """
    ).fetchall()

    traits: dict[int, DbTrait] = dict()

    for r in rows:
        thresholds = [int(x) for x in r["thresholds"].split(",")]
        thresholds.sort()

        traits[r["id"]] = DbTrait(id=r["id"], name=r["name"], thresholds=thresholds)

    return traits


@dataclass
class DbChampion:
    id: int
    cost: int
    name: str

    traits: list[int]

    def __hash__(self) -> int:
        return self.id


def get_all_champions(db: Database) -> dict[int, DbChampion]:
    rows = db.execute(
        """
        SELECT c.id, c.cost, c.name, GROUP_CONCAT(t.id_trait) as traits FROM champions c
        LEFT JOIN champion_traits t ON t.id_champion = c.id
        GROUP BY c.id 
        """
    ).fetchall()

    champions: list[DbChampion] = []
    for r in rows:
        data = dict(r)
        data["traits"] = [int(id) for id in data["traits"].split(",")]
        champions.append(DbChampion(**data))

    return {c.id: c for c in champions}


def get_champions_by_trait(
    champions: Iterable[DbChampion],
) -> dict[int, list[DbChampion]]:
    result: dict[int, list[DbChampion]] = dict()

    for champ in champions:
        for trait in champ.traits:
            result.setdefault(trait, [])
            result[trait].append(champ)

    return result
