import OpenAI from 'openai';
import { AppEnv } from '../config/env.js';
import { Result, err, ok } from '../types/result.js';

export type LlmMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export type LlmResponse = {
  text: string;
  usage: {
    inputTokens: number;
    outputTokens: number;
  };
};

export class LlmClient {
  private readonly client: OpenAI;

  public constructor(private readonly env: AppEnv) {
    this.client = new OpenAI({ apiKey: env.OPENAI_API_KEY });
  }

  public async generate(messages: LlmMessage[]): Promise<Result<LlmResponse, string>> {
    try {
      const completion = await this.client.responses.create({
        model: this.env.OPENAI_MODEL,
        input: messages.map((message) => ({ role: message.role, content: message.content })),
      });

      return ok({
        text: completion.output_text,
        usage: {
          inputTokens: completion.usage?.input_tokens ?? 0,
          outputTokens: completion.usage?.output_tokens ?? 0,
        },
      });
    } catch (error) {
      return err(error instanceof Error ? error.message : 'LLM generation failed');
    }
  }
}
