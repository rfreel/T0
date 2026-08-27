import { LlmClient } from '../core/llmClient.js';
import { withSpan } from '../telemetry/tracing.js';
import { Result, err, ok } from '../types/result.js';
import { SqliteStore } from '../storage/sqlite.js';
import { approximateTokenCount, computeDriftScore } from './drift.js';
import { MemorySnapshot } from './types.js';

export class MemoryEngine {
  public constructor(
    private readonly store: SqliteStore,
    private readonly llm: LlmClient,
    private readonly shortTermLimit: number,
  ) {}

  public remember(role: 'system' | 'user' | 'assistant' | 'tool', content: string): number {
    return this.store.insertMessage(role, content, approximateTokenCount(content));
  }

  public snapshot(): MemorySnapshot {
    return {
      shortTerm: this.store.latestMessages(this.shortTermLimit).reverse(),
      observations: this.store.latestObservations(10).reverse(),
      reflections: this.store.latestReflections(5).reverse(),
    };
  }

  public async observe(sourceMessageIds: number[]): Promise<Result<number, string>> {
    return withSpan('memory.observe', {}, async (span) => {
      const messages = this.store.latestMessages(this.shortTermLimit).reverse();
      const conversation = messages.map((message) => `${message.role}: ${message.content}`).join('\n');
      const observationPrompt = [
        { role: 'system' as const, content: 'Create a dense temporal observation from the chat excerpt.' },
        { role: 'user' as const, content: conversation },
      ];

      const result = await this.llm.generate(observationPrompt);
      if (!result.ok) {
        return err(result.error);
      }

      const driftScore = computeDriftScore(messages[0]?.content ?? '', result.value.text);
      span.setAttribute('agent.memory.drift_score', driftScore);
      const observationId = this.store.insertObservation(sourceMessageIds, result.value.text, driftScore);
      return ok(observationId);
    });
  }

  public async reflect(): Promise<Result<number, string>> {
    return withSpan('memory.reflect', {}, async (_span) => {
      const observations = this.store.latestObservations(20).reverse();
      if (observations.length === 0) {
        return err('No observations available for reflection');
      }

      const reflectionPrompt = [
        { role: 'system' as const, content: 'Synthesize the observations into high-level reflections and stable context anchors.' },
        { role: 'user' as const, content: observations.map((entry) => entry.content).join('\n---\n') },
      ];

      const reflection = await this.llm.generate(reflectionPrompt);
      if (!reflection.ok) {
        return err(reflection.error);
      }

      const reflectionId = this.store.insertReflection(observations.map((entry) => entry.id), reflection.value.text);
      return ok(reflectionId);
    });
  }
}
