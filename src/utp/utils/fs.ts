import { mkdir, writeFile } from 'node:fs/promises';

export const utcRunId = (): string => new Date().toISOString().replace(/[:]/g, '-');

const stableSerialize = (value: unknown): string => {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(',')}]`;
  }

  const entries = Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b));
  return `{${entries.map(([key, nested]) => `${JSON.stringify(key)}:${stableSerialize(nested)}`).join(',')}}`;
};

export const writeJsonDeterministic = async (path: string, value: unknown): Promise<void> => {
  await writeFile(path, `${stableSerialize(value)}\n`, 'utf8');
};

export const ensureDir = async (path: string): Promise<void> => {
  await mkdir(path, { recursive: true });
};
