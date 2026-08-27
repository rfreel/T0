import { AppEnv } from '../config/env.js';
import { ContextRepl } from './contextRepl.js';
import { MemoryEngine } from './memoryEngine.js';
import { ContextPatch } from './types.js';

export class ReflectorLoop {
  private timer: NodeJS.Timeout | undefined;
  private activeInstructions: string;

  public constructor(
    private readonly env: AppEnv,
    private readonly memory: MemoryEngine,
    private readonly repl: ContextRepl,
    baseInstructions: string,
  ) {
    this.activeInstructions = baseInstructions;
  }

  public start(): void {
    this.timer = setInterval(() => {
      void this.tick();
    }, this.env.REFLECTION_INTERVAL_MS);
  }

  public stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
  }

  public instructions(): string {
    return this.activeInstructions;
  }

  private async tick(): Promise<void> {
    const reflectionResult = await this.memory.reflect();
    if (!reflectionResult.ok) {
      return;
    }

    const latestReflection = this.memory.snapshot().reflections.at(-1);
    if (!latestReflection) {
      return;
    }

    const patches: ContextPatch[] = [
      {
        operation: 'append',
        content: `\n[Reflector Anchor]\n${latestReflection.content}`,
      },
    ];

    this.activeInstructions = this.repl.apply(this.activeInstructions, patches);
  }
}
