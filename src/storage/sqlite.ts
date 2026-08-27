import Database from 'better-sqlite3';
import { AppEnv } from '../config/env.js';
import { schemaSql, MessageRecord, ObservationRecord, ReflectionRecord } from './schema.js';

export class SqliteStore {
  private readonly db: Database.Database;

  public constructor(env: AppEnv) {
    this.db = new Database(env.SQLITE_PATH);
    this.db.pragma('journal_mode = WAL');
    this.db.exec(schemaSql);
  }

  public insertMessage(role: MessageRecord['role'], content: string, tokenCount: number): number {
    const row = this.db
      .prepare('INSERT INTO messages (role, content, token_count) VALUES (?, ?, ?) RETURNING id')
      .get(role, content, tokenCount) as { id: number };
    return row.id;
  }

  public latestMessages(limit: number): MessageRecord[] {
    return this.db
      .prepare('SELECT * FROM messages ORDER BY id DESC LIMIT ?')
      .all(limit) as MessageRecord[];
  }

  public insertObservation(sourceMessageIds: number[], content: string, driftScore: number): number {
    const row = this.db
      .prepare('INSERT INTO observations (source_message_ids, content, drift_score) VALUES (?, ?, ?) RETURNING id')
      .get(JSON.stringify(sourceMessageIds), content, driftScore) as { id: number };
    return row.id;
  }

  public latestObservations(limit: number): ObservationRecord[] {
    return this.db
      .prepare('SELECT * FROM observations ORDER BY id DESC LIMIT ?')
      .all(limit) as ObservationRecord[];
  }

  public insertReflection(observationIds: number[], content: string): number {
    const row = this.db
      .prepare('INSERT INTO reflections (observation_ids, content) VALUES (?, ?) RETURNING id')
      .get(JSON.stringify(observationIds), content) as { id: number };
    return row.id;
  }

  public latestReflections(limit: number): ReflectionRecord[] {
    return this.db
      .prepare('SELECT * FROM reflections ORDER BY id DESC LIMIT ?')
      .all(limit) as ReflectionRecord[];
  }

  public insertTrace(spanName: string, payload: Record<string, unknown>): void {
    this.db.prepare('INSERT INTO traces (span_name, payload) VALUES (?, ?)').run(spanName, JSON.stringify(payload));
  }
}
