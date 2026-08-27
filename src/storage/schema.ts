export const schemaSql = `
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_message_ids TEXT NOT NULL,
  content TEXT NOT NULL,
  drift_score REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reflections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  observation_ids TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS traces (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  span_name TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
`;

export type MessageRecord = {
  id: number;
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  token_count: number;
  created_at: string;
};

export type ObservationRecord = {
  id: number;
  source_message_ids: string;
  content: string;
  drift_score: number;
  created_at: string;
};

export type ReflectionRecord = {
  id: number;
  observation_ids: string;
  content: string;
  created_at: string;
};
