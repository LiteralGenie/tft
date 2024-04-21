import sqlite3
from typing import TypeAlias

from config import DB_FILE
from data import ALL_CHAMPIONS, ALL_TRAITS

Database: TypeAlias = sqlite3.Connection


def init_db():
    db = sqlite3.connect(DB_FILE)

    db.row_factory = sqlite3.Row

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS champions (
            id      INTEGER     PRIMARY KEY,

            cost    INTEGER     NOT NULL,
            name    TEXT        NOT NULL
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

    for trait in ALL_TRAITS.__dict__.values():
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

    for champion in ALL_CHAMPIONS:
        db.execute(
            """
            INSERT INTO CHAMPIONS
                (id, cost, name) VALUES
                (?, ?, ?)
            """,
            [champion.id, champion.cost, champion.name],
        )

        for trait in champion.traits:
            db.execute(
                """
                INSERT INTO champion_traits
                    (id_champion, id_trait) VALUES
                    (?, ?)
                """,
                [champion.id, trait.id],
            )


def table_exists(db: Database, name: str) -> bool:
    result = db.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table' AND name='?'
        """,
        [name],
    )

    return result != None
