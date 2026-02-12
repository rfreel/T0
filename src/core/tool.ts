import { Result } from '../types/result.js';

export type Tool<TInput, TOutput> = {
  name: string;
  description: string;
  execute: (input: TInput) => Promise<Result<TOutput, string>>;
};
