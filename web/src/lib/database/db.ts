import SQLite from 'better-sqlite3'
import { DeduplicateJoinsPlugin, Kysely, SqliteDialect } from 'kysely'
import type { Database } from './types.ts'

const dialect = new SqliteDialect({
    database: new SQLite(process.env.DB_FILE)
})

export const db = new Kysely<Database>({
    dialect,
    plugins: [new DeduplicateJoinsPlugin()]
})
