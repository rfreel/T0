import { z } from 'zod';
import { Result, err, ok } from '../types/result.js';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  OPENAI_API_KEY: z.string().min(1, 'OPENAI_API_KEY is required'),
  OPENAI_MODEL: z.string().default('gpt-4o-mini'),
  SQLITE_PATH: z.string().default('./rlm.db'),
  OBSERVER_TOKEN_THRESHOLD: z.coerce.number().int().positive().default(800),
  SHORT_TERM_LIMIT: z.coerce.number().int().positive().default(12),
  REFLECTION_INTERVAL_MS: z.coerce.number().int().positive().default(30000),
  OBSERVER_POLL_MS: z.coerce.number().int().positive().default(2000),
  TRACE_FILE_PATH: z.string().default('./traces.ndjson'),
});

export type AppEnv = z.infer<typeof envSchema>;

export const loadEnv = (): Result<AppEnv, string> => {
  const parsed = envSchema.safeParse(process.env);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((issue) => `${issue.path.join('.')}: ${issue.message}`).join('; ');
    return err(`Environment validation failed: ${issues}`);
  }
  return ok(parsed.data);
};
