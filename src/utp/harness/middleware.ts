import { appendFile } from 'node:fs/promises';
import { ToolMiddleware } from './types.js';

export const schemaValidationMiddleware = (): ToolMiddleware => ({
  beforeCall: async (call) => {
    if (typeof call.args !== 'object' || call.args === null) {
      throw new Error('SchemaValidationError: tool args must be a JSON object.');
    }
    return call;
  },
});

export const determinismMiddleware = (): ToolMiddleware => ({
  beforeCall: async (call, context) => ({
    ...call,
    args: typeof call.args === 'object' && call.args !== null
      ? Object.fromEntries(Object.entries(call.args as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b)))
      : call.args,
    callId: `${context.phase}-${context.seed}-${call.callId}`,
  }),
});

export const auditTrailMiddleware = (logPath: string): ToolMiddleware => ({
  beforeCall: async (call, context) => {
    await appendFile(logPath, `${JSON.stringify({ event: 'tool_call', phase: context.phase, call })}\n`, 'utf8');
    return call;
  },
  afterCall: async (_call, result, context) => {
    await appendFile(logPath, `${JSON.stringify({ event: 'tool_result', phase: context.phase, result })}\n`, 'utf8');
    return result;
  },
});
