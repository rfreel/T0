import { EventEmitter } from 'node:events';
import { AppEnv } from '../config/env.js';
import { MemoryEngine } from '../memory/memoryEngine.js';
import { ReflectorLoop } from '../memory/reflectorLoop.js';
import { withSpan } from '../telemetry/tracing.js';
import { Result, err, ok } from '../types/result.js';
import { AgentEvent, EventHandler } from './events.js';
import { LlmClient } from './llmClient.js';
import { Tool } from './tool.js';

export type BaseAgentOptions = {
  name: string;
  instructions: string;
  tools: Tool<unknown, unknown>[];
  env: AppEnv;
  llm: LlmClient;
  memory: MemoryEngine;
  reflector: ReflectorLoop;
};

export class BaseAgent {
  private readonly emitter = new EventEmitter();

  public constructor(private readonly options: BaseAgentOptions) {}

  public onEvent(handler: EventHandler): void {
    this.emitter.on('event', handler);
  }

  public async run(input: string): Promise<Result<string, string>> {
    this.emit({ type: 'start', input });
    this.options.memory.remember('user', input);

    if (input.startsWith('/tool ')) {
      const toolResult = await this.invokeTool(input);
      if (!toolResult.ok) {
        return toolResult;
      }
      this.emit({ type: 'finish', output: toolResult.value });
      return toolResult;
    }

    const injectedPrompt = this.injectMemoryContext();

    const output = await withSpan(
      'agent.generate',
      {
        'gen_ai.system.model_name': this.options.env.OPENAI_MODEL,
      },
      async (span) => {
        const result = await this.options.llm.generate([
          { role: 'system', content: injectedPrompt },
          { role: 'user', content: input },
        ]);
        if (result.ok) {
          span.setAttribute('gen_ai.usage.input_tokens', result.value.usage.inputTokens);
        }
        return result;
      },
    );

    if (!output.ok) {
      return err(output.error);
    }

    const response = output.value.text;
    this.emitTokens(response);
    this.options.memory.remember('assistant', response);
    this.emit({ type: 'finish', output: response });

    return ok(response);
  }

  private async invokeTool(input: string): Promise<Result<string, string>> {
    const [, toolName, ...payloadParts] = input.split(' ');
    const payload = payloadParts.join(' ');
    const tool = this.options.tools.find((item) => item.name === toolName);

    if (!tool) {
      return err(`Unknown tool: ${toolName}`);
    }

    const output = await withSpan(
      'tool.execute',
      {
        'tool.name': tool.name,
      },
      () => tool.execute(payload),
    );

    if (!output.ok) {
      return err(output.error);
    }

    const toolText = String(output.value);
    this.options.memory.remember('tool', toolText);
    this.emit({ type: 'tool', toolName, payload: output.value });
    return ok(toolText);
  }

  private injectMemoryContext(): string {
    const snapshot = this.options.memory.snapshot();
    const reflections = snapshot.reflections.map((reflection) => `- ${reflection.content}`).join('\n');
    const observations = snapshot.observations.slice(-3).map((observation) => `- ${observation.content}`).join('\n');

    return [
      this.options.reflector.instructions(),
      '[RLM: Observations]',
      observations || '- none',
      '[RLM: Reflections]',
      reflections || '- none',
    ].join('\n');
  }

  private emitTokens(text: string): void {
    for (const token of text.split(/\s+/).filter(Boolean)) {
      this.emit({ type: 'token', token });
    }
  }

  private emit(event: AgentEvent): void {
    this.emitter.emit('event', event);
  }
}
