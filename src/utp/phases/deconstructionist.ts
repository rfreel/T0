import { z } from 'zod';
import { err, ok, Result } from '../../types/result.js';
import { pipelineInputSchema, StructuralLogicMap, structuralLogicMapSchema } from '../models.js';

export const requiredTools = () => ['extract_keywords'];

export const runDeconstructionist = async (input: z.infer<typeof pipelineInputSchema>): Promise<Result<StructuralLogicMap, string>> => {
  const parsed = pipelineInputSchema.safeParse(input);
  if (!parsed.success) {
    return err(parsed.error.message);
  }

  const lines = parsed.data.sourceArtifact.split('\n').map((line) => line.trim()).filter(Boolean);
  const transitions = lines.length === 0
    ? ['Preconditions -> Parse -> Emit artifacts']
    : lines.slice(0, 5).map((line, index) => `T${index + 1}: ${line}`);

  const candidate = {
    interfaces: `input:${parsed.data.sourceDomain} output:${parsed.data.targetDomain}`,
    state: 'mutable: phase payloads; immutable: section order',
    transitions,
    constraints: ['five fixed output sections', 'strict schema validation', 'deterministic run folder'],
    failureModes: ['schema mismatch', 'tool args invalid', 'missing evidence artifacts'],
  };

  const valid = structuralLogicMapSchema.safeParse(candidate);
  if (!valid.success) {
    return err(valid.error.message);
  }
  return ok(valid.data);
};
