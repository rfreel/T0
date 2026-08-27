import { Result } from '../types/result.js';

export type CallableAgent<TInput, TOutput> = {
  id: string;
  description: string;
  call: (input: TInput) => Promise<Result<TOutput, string>>;
};
