import { db } from '../db'
import { toSqliteBool } from '../utils'

export const PAGE_SIZE = 100

export type ChampionCost = 1 | 2 | 3 | 4 | 5

export interface SingleChampionFilter {
    type: 'single'
    id?: number
}

export interface VariableChampionFilter {
    type: 'variable'
    costs?: ChampionCost[]
    damageType?: 'ad' | 'ap'
    rangeType?: 'melee' | 'semi-ranged' | 'ranged'
    traits?: {
        ids: number[]
        mode: 'or' | 'and'
    }
}

export type ChampionFilter = SingleChampionFilter | VariableChampionFilter

export interface SearchCompsOptions {
    offset?: number

    sizes?: number[]
    max_cost?: number
    champions?: ChampionFilter[]
}

export interface CompositionSearchResult {
    id: number
    id_champions: number[]
}

export async function searchComps(opts?: SearchCompsOptions): Promise<CompositionSearchResult[]> {
    // Select all comps
    let query = db
        .selectFrom('compositions as c')
        .innerJoin('composition_champions as cc', 'cc.id_composition', 'c.id')
        .groupBy('c.id')
        .select(({ fn }) => [
            'c.id',
            fn.agg<string>('group_concat', ['cc.id_champion']).as('id_champions')
        ])
        .limit(PAGE_SIZE)

    // Filter by size
    for (let sz of opts?.sizes ?? []) {
        query = query.where('c.size', '=', sz)
    }

    // Filter by cost
    if (opts?.max_cost) {
        query = query
            .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
            .having(({ fn }) => fn.max('ch.cost'), '<=', opts.max_cost)
    }

    // Per-champion filters
    for (let filter of opts?.champions ?? []) {
        if (filter.type === 'single') {
            query = query.having(({ fn }) => fn.max('cc.id_champion'), '=', filter.id)
        } else {
            // Costs
            if (filter.costs) {
                query = query
                    .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                    .having('ch.cost', 'in', filter.costs)
            }

            // Damage type
            if (filter.damageType) {
                query = query
                    .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                    .having('ch.uses_ap', 'in', toSqliteBool(filter.damageType === 'ad'))
            }

            // Range
            switch (filter.rangeType) {
                case 'melee':
                    query = query
                        .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                        .having('ch.range', '=', 1)
                    break
                case 'semi-ranged':
                    query = query
                        .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                        .having('ch.range', '=', 2)
                    break
                case 'ranged':
                    query = query
                        .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                        .having('ch.range', '>', 2)
                    break
            }

            // Traits
            if (filter.traits) {
                query = query
                    .innerJoin('champions as ch', 'ch.id', 'cc.id_champion')
                    .having('ch.uses_ap', 'in', toSqliteBool(filter.damageType === 'ad'))
            }
        }
    }

    // Filter by offset
    if (opts?.offset) {
        query = query.offset(opts.offset)
    }

    const rows = await query.execute()

    const parsed = rows.map((r) => ({
        ...r,
        id_champions: r.id_champions.split(',').map((s) => parseInt(s))
    }))

    return parsed
}
