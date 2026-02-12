import { err, ok, Result } from '../../types/result.js';
import { MediumAgnosticSpec, mediumAgnosticSpecSchema, StructuralLogicMap } from '../models.js';

export const requiredTools = () => ['transition_mapper'];

export const runOntologist = async (input: StructuralLogicMap): Promise<Result<MediumAgnosticSpec, string>> => {
  const candidate = {
    glossary: [
      { term: 'Entity', definition: 'Unit carrying input or output state.' },
      { term: 'Constraint', definition: 'Invariant that must hold.' },
      { term: 'Event', definition: 'Trigger that advances phase.' },
      { term: 'Transformation', definition: 'Operation mapping state to state.' },
      { term: 'Store', definition: 'Persisted artifact container.' },
      { term: 'Check', definition: 'Observable verification action.' },
    ],
    requirements: input.transitions.map((transition, idx) => ({
      id: `R${idx + 1}`,
      givenWhenThen: `Given valid input, when transition executes (${transition}), then an artifact update is produced.`,
      preconditions: 'Input schema valid and prior phase completed.',
      guarantees: 'Output conforms to strict model schema.',
      observables: `run.ndjson contains transition marker for ${transition}.`,
      coversTransitions: [transition],
    })),
    nonFunctionalConstraints: [
      'Deterministic ordering for all serialized JSON keys.',
      'All runs persist evidence artifacts in per-run directory.',
      'No extra fields beyond schema contracts.',
    ],
    conformanceTests: [
      {
        id: 'T1',
        validatesRequirements: ['R1'],
        procedure: 'Validate structural_logic_map.json against schema.',
        expected: 'Schema pass.',
      },
      {
        id: 'T2',
        validatesRequirements: ['R1'],
        procedure: 'Validate every transition appears in at least one requirement.coversTransitions entry.',
        expected: 'Complete coverage.',
      },
      {
        id: 'T3',
        validatesRequirements: ['R1'],
        procedure: 'Validate target artifact and run hooks exist.',
        expected: 'Artifact complete.',
      },
      {
        id: 'T4',
        validatesRequirements: ['R1'],
        procedure: 'Validate discrepancies empty for accepted golden example.',
        expected: 'No discrepancies.',
      },
    ],
  };

  const valid = mediumAgnosticSpecSchema.safeParse(candidate);
  if (!valid.success) {
    return err(valid.error.message);
  }
  return ok(valid.data);
};
