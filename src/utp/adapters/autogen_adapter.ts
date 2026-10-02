import { ToolRegistry } from '../harness/toolRegistry.js';

export type AutoGenAdapter = {
  kind: 'autogen';
  registry: ToolRegistry;
  transcript: string[];
  registerSchemas: () => string[];
};

export const createAutoGenAdapter = (registry: ToolRegistry): AutoGenAdapter => ({
  kind: 'autogen',
  registry,
  transcript: [],
  registerSchemas: () => registry.list(),
});
