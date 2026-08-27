import { createAutoGenAdapter } from './autogen_adapter.js';
import { createRawChatAdapter } from './raw_chat_adapter.js';
import { ToolRegistry } from '../harness/toolRegistry.js';

export const loadAdapter = (kind: 'raw' | 'autogen', registry: ToolRegistry) =>
  kind === 'autogen' ? createAutoGenAdapter(registry) : createRawChatAdapter(registry);
