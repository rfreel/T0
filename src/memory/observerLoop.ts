import { AppEnv } from '../config/env.js';
import { MemoryEngine } from './memoryEngine.js';

export class ObserverLoop {
  private timer: NodeJS.Timeout | undefined;
  private running = false;

  public constructor(
    private readonly env: AppEnv,
    private readonly memory: MemoryEngine,
  ) {}

  public start(): void {
    if (this.running) {
      return;
    }

    this.running = true;
    this.timer = setInterval(() => {
      void this.tick();
    }, this.env.OBSERVER_POLL_MS);
  }

  public stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = undefined;
    }
    this.running = false;
  }

  private async tick(): Promise<void> {
    const snapshot = this.memory.snapshot();
    const tokenBudget = snapshot.shortTerm.reduce((sum, message) => sum + message.token_count, 0);

    if (tokenBudget < this.env.OBSERVER_TOKEN_THRESHOLD) {
      return;
    }

    const sourceIds = snapshot.shortTerm.map((message) => message.id);
    await this.memory.observe(sourceIds);
  }
}
