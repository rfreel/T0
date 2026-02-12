import { mkdir, writeFile } from 'node:fs/promises';

export const utcRunId = (): string => new Date().toISOString().replace(/[:]/g, '-');

export const writeJsonDeterministic = async (path: string, value: unknown): Promise<void> => {
  const stable = JSON.stringify(value, Object.keys(value as Record<string, unknown>).sort(), 2);
  await writeFile(path, `${stable}\n`, 'utf8');
};

export const ensureDir = async (path: string): Promise<void> => {
  await mkdir(path, { recursive: true });
};
