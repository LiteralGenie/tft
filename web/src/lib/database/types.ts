// No nominal types so this is just for readability
export type SqliteInteger = number
export type SqliteReal = number

export type SqliteBool = 0 | 1

export interface Database {
    champions: ChampionsTable
    traits: TraitsTable
    trait_thresholds: TraitThresholdsTable
    champion_traits: ChampionTraitsTable
    compositions: CompositionsTable
    composition_champions: CompositionChampionsTable
    scores_by_trait: ScoresByTraitTable
}

export interface ChampionsTable {
    id: number

    cost: SqliteInteger
    name: string
    range: SqliteInteger
    uses_ap: SqliteBool
}

export interface TraitsTable {
    id: number

    name: string
}

export interface TraitThresholdsTable {
    id: number
    id_trait: number

    threshold: SqliteInteger
}

export interface ChampionTraitsTable {
    id_champion: number
    id_trait: number
}

export interface CompositionsTable {
    id: number

    hash: string
    is_expanded: SqliteBool
    size: SqliteInteger
}

export interface CompositionChampionsTable {
    id_composition: number
    id_champion: number
}

export interface ScoresByTraitTable {
    id_composition: number

    score: SqliteReal
}
