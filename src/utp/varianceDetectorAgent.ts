import { ok, Result } from '../types/result.js';
import { CallableAgent } from './callableAgent.js';
import { AuditResult, MediumAgnosticSpec, StructuralLogicMap } from './types.js';

export type VarianceDetectorInput = {
  map: StructuralLogicMap;
  spec: MediumAgnosticSpec;
  artifact: string;
};

const hasAllStructuralFields = (map: StructuralLogicMap): boolean =>
  [map.Interfaces, map.State, map.Transitions, map.Constraints, map.FailureModes].every((value) => value.trim().length > 0);

const detectDiscrepancies = (input: VarianceDetectorInput): string[] => {
  const discrepancies: string[] = [];

  if (!hasAllStructuralFields(input.map)) {
    discrepancies.push('D1: Missing non-empty field in structural map (violates R1).');
  }

  if (!input.spec.Requirements.some((requirement) => requirement.id === 'R2')) {
    discrepancies.push('D2: Transition coverage requirement missing (violates R2).');
  }

  if (!input.artifact.includes('Callable multi-agent transpilation pipeline')) {
    discrepancies.push('D3: Target artifact not recognized as callable pipeline deliverable (violates R3).');
  }

  return discrepancies;
};

export class VarianceDetectorAgent implements CallableAgent<VarianceDetectorInput, AuditResult> {
  public readonly id = 'Variance_Detector';
  public readonly description = 'Audits conformance tests and emits discrepancies and patch instructions context.';

  public async call(input: VarianceDetectorInput): Promise<Result<AuditResult, string>> {
    const discrepancies = detectDiscrepancies(input);

    const testResults = [
      `T1: ${hasAllStructuralFields(input.map) ? 'pass' : 'fail'} | evidence: structural field completeness check`,
      `T2: ${input.spec.Requirements.some((requirement) => requirement.id === 'R2') ? 'pass' : 'fail'} | evidence: requirements include transition coverage`,
      `T3: ${input.artifact.includes('Modules:') ? 'pass' : 'fail'} | evidence: target artifact module list`,
      `T4: ${discrepancies.length === 0 ? 'pass' : 'fail'} | evidence: discrepancy count=${discrepancies.length}`,
    ];

    const audit: AuditResult = {
      TestResults: testResults,
      Discrepancies: discrepancies,
      RootCauseHypotheses: discrepancies.length === 0
        ? ['H0: No mismatch detected between requirements and generated artifact under available checks.']
        : [
            'H1: Upstream phase emitted incomplete payload (falsify by re-running with payload snapshots).',
            'H2: Domain artifact template omitted required callable pipeline markers.',
          ],
      Severity: discrepancies.length === 0 ? 'must-fix: none' : 'must-fix: present discrepancies block acceptance',
    };

    return ok(audit);
  }
}
