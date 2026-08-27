import { MessageRecord, ObservationRecord, ReflectionRecord } from '../storage/schema.js';

export type MemorySnapshot = {
  shortTerm: MessageRecord[];
  observations: ObservationRecord[];
  reflections: ReflectionRecord[];
};

export type ContextPatch = {
  operation: 'append' | 'replace';
  content: string;
};
