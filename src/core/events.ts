export type AgentEvent =
  | { type: 'start'; input: string }
  | { type: 'token'; token: string }
  | { type: 'tool'; toolName: string; payload: unknown }
  | { type: 'finish'; output: string };

export type EventHandler = (event: AgentEvent) => void;
