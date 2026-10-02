import { z } from 'zod';

export type JsonSchemaLike = z.ZodTypeAny;

export type Tool<TArgs extends z.ZodTypeAny = z.ZodTypeAny> = {
  name: string;
  description: string;
  jsonSchema: TArgs;
  callable: (args: z.infer<TArgs>) => Promise<unknown>;
};

export type ToolCall = {
  toolName: string;
  args: unknown;
  callId: string;
};

export type ToolResult = {
  callId: string;
  ok: boolean;
  output?: unknown;
  error?: string;
};

export type MiddlewareContext = {
  phase: string;
  seed: number;
};

export type ToolMiddleware = {
  beforeCall?: (call: ToolCall, context: MiddlewareContext) => Promise<ToolCall>;
  afterCall?: (call: ToolCall, result: ToolResult, context: MiddlewareContext) => Promise<ToolResult>;
};
