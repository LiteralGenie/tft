import SQLite from 'better-sqlite3'
import { Kysely, SqliteDialect } from 'kysely'
import type { Database } from './types.ts' // this is the Database interface we defined earlier

const fp = process.env.NODE_ENV === 'production' ? '/app/src/data/db.sqlite' : process.env.DB_FILE
export const dbConn = new SQLite(fp)

const dialect = new SqliteDialect({
    database: dbConn
})

export const db = new Kysely<Database>({
    dialect
})
