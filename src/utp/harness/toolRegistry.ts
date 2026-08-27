import { ZodError } from 'zod';
import { err, ok, Result } from '../../types/result.js';
import { Tool, ToolCall, ToolMiddleware, ToolResult } from './types.js';

export class ToolRegistry {
  private readonly tools = new Map<string, Tool>();

  public register(tool: Tool): void {
    this.tools.set(tool.name, tool);
  }

  public resolve(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  public subset(allowed: string[]): ToolRegistry {
    const subset = new ToolRegistry();
    for (const name of allowed) {
      const tool = this.tools.get(name);
      if (tool) {
        subset.register(tool);
      }
    }
    return subset;
  }

  public list(): string[] {
    return [...this.tools.keys()].sort();
  }
}

const zodMessage = (error: ZodError): string =>
  error.issues.map((issue) => `${issue.path.join('.') || '<root>'}: ${issue.message}`).join('; ');

export class Harness {
  public constructor(
    private readonly registry: ToolRegistry,
    private readonly middleware: ToolMiddleware[],
    private readonly phase: string,
    private readonly seed = 7,
  ) {}

  public async callTool(call: ToolCall): Promise<Result<ToolResult, string>> {
    const tool = this.registry.resolve(call.toolName);
    if (!tool) {
      return err(`Unknown tool: ${call.toolName}`);
    }

    let currentCall = call;
    for (const handler of this.middleware) {
      if (handler.beforeCall) {
        currentCall = await handler.beforeCall(currentCall, { phase: this.phase, seed: this.seed });
      }
    }

    try {
      const parsed = tool.jsonSchema.parse(currentCall.args);
      const output = await tool.callable(parsed);
      let result: ToolResult = { callId: currentCall.callId, ok: true, output };
      for (const handler of this.middleware) {
        if (handler.afterCall) {
          result = await handler.afterCall(currentCall, result, { phase: this.phase, seed: this.seed });
        }
      }
      return ok(result);
    } catch (error) {
      const schemaError = error instanceof ZodError ? `SchemaValidationError: ${zodMessage(error)}` : undefined;
      let result: ToolResult = {
        callId: currentCall.callId,
        ok: false,
        error: schemaError ?? (error instanceof Error ? error.message : 'tool execution failed'),
      };
      for (const handler of this.middleware) {
        if (handler.afterCall) {
          result = await handler.afterCall(currentCall, result, { phase: this.phase, seed: this.seed });
        }
      }
      return err(result.error ?? 'tool execution failed');
    }
  }
}
