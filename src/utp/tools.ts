import { z } from 'zod';
import { ToolRegistry } from './harness/toolRegistry.js';

export const createDefaultToolRegistry = (): ToolRegistry => {
  const registry = new ToolRegistry();

  registry.register({
    name: 'extract_keywords',
    description: 'Extract keyword hints from text.',
    jsonSchema: z.object({ text: z.string() }).strict(),
    callable: async ({ text }) => text.split(/\W+/).filter(Boolean).slice(0, 5),
  });

  registry.register({
    name: 'transition_mapper',
    description: 'Maps transitions to requirement identifiers.',
    jsonSchema: z.object({ transitions: z.array(z.string()) }).strict(),
    callable: async ({ transitions }) => transitions.map((transition, i) => ({ requirementId: `R${i + 1}`, transition })),
  });

  registry.register({
    name: 'artifact_renderer',
    description: 'Renders target artifact body.',
    jsonSchema: z.object({ lines: z.array(z.string()) }).strict(),
    callable: async ({ lines }) => lines.join('\n'),
  });

  registry.register({
    name: 'evidence_reader',
    description: 'Returns evidence digest.',
    jsonSchema: z.object({ path: z.string() }).strict(),
    callable: async ({ path }) => `evidence:${path}`,
  });

  return registry;
};
