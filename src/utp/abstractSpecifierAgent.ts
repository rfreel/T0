import { ok, Result } from '../types/result.js';
import { CallableAgent } from './callableAgent.js';
import { MediumAgnosticSpec, Requirement, StructuralLogicMap } from './types.js';

const buildRequirements = (map: StructuralLogicMap): Requirement[] => [
  {
    id: 'R1',
    givenWhenThen: 'Given validated input entities, when the pipeline starts, then structural decomposition is emitted with Interfaces/State/Transitions/Constraints/FailureModes.',
    preconditions: 'Entity Source is non-empty text.',
    guarantees: 'Every structural field is present exactly once.',
    observables: 'STRUCTURAL_LOGIC_MAP contains all required headings.',
  },
  {
    id: 'R2',
    givenWhenThen: 'Given structural decomposition, when abstraction runs, then requirement set and tests are generated using universal vocabulary.',
    preconditions: 'R1 output exists.',
    guarantees: 'All transitions are covered by one or more requirements.',
    observables: `Requirements reference transition evidence from map: ${map.Transitions.slice(0, 120)}...`,
  },
  {
    id: 'R3',
    givenWhenThen: 'Given abstract requirements, when native creation executes, then a complete target artifact is produced with runtime hooks.',
    preconditions: 'R2 output exists.',
    guarantees: 'Artifact is complete and executable in target environment assumptions.',
    observables: 'TARGET_ARTIFACT includes module structure and callable entrypoint.',
  },
  {
    id: 'R4',
    givenWhenThen: 'Given target artifact, when audit executes, then conformance tests report pass/fail with evidence and discrepancy mapping.',
    preconditions: 'R3 output exists.',
    guarantees: 'Audit emits tests, discrepancies, hypotheses, severity, and patch instructions.',
    observables: 'AUDIT_REPORT and PATCH_INSTRUCTIONS sections are present and structured.',
  },
];

export class AbstractSpecifierAgent implements CallableAgent<StructuralLogicMap, MediumAgnosticSpec> {
  public readonly id = 'Abstract_Specifier';
  public readonly description = 'Creates medium-agnostic requirements, constraints, and conformance tests.';

  public async call(input: StructuralLogicMap): Promise<Result<MediumAgnosticSpec, string>> {
    const spec: MediumAgnosticSpec = {
      Glossary: 'Entity: identifiable unit; Constraint: invariant rule; Event: trigger signal; Transformation: state change; Store: persisted state; Check: observable proof step.',
      Requirements: buildRequirements(input),
      NonFunctionalConstraints: 'Deterministic section order; bounded memory by explicit phase context; traceability from requirement to test; minimal edits for remediation.',
      ConformanceTests: [
        'T1 validates structural headings and non-empty values for all required fields.',
        'T2 validates each transition has requirement coverage (R2).',
        'T3 validates target artifact completeness and callable entrypoint details.',
        'T4 validates audit output includes pass/fail evidence and discrepancy mapping.',
      ],
    };

    return ok(spec);
  }
}
