import { ToolRegistry } from '../harness/toolRegistry.js';

export type RawChatAdapter = {
  kind: 'raw';
  registry: ToolRegistry;
  transcript: string[];
};

export const createRawChatAdapter = (registry: ToolRegistry): RawChatAdapter => ({
  kind: 'raw',
  registry,
  transcript: [],
});
