import { ok, Result } from '../types/result.js';
import { CallableAgent } from './callableAgent.js';
import { MediumAgnosticSpec, UtpInput } from './types.js';

export type DomainSpecialistInput = {
  request: UtpInput;
  spec: MediumAgnosticSpec;
};

export class DomainSpecialistAgent implements CallableAgent<DomainSpecialistInput, string> {
  public readonly id = 'Domain_Specialist';
  public readonly description = 'Builds a native target artifact from medium-agnostic requirements.';

  public async call(input: DomainSpecialistInput): Promise<Result<string, string>> {
    const requirements = input.spec.Requirements.map((requirement) => `- ${requirement.id}: ${requirement.givenWhenThen}`).join('\n');

    const artifact = [
      `TargetDomain: ${input.request.targetDomain}`,
      `TargetEnvironment: ${input.request.targetEnvironment}`,
      'Deliverable: Callable multi-agent transpilation pipeline',
      'Modules:',
      '- structuralAnalyst.call(input) -> structural map',
      '- abstractSpecifier.call(structural) -> agnostic spec',
      '- domainSpecialist.call(spec) -> target artifact',
      '- varianceDetector.call(all) -> audit + patch instructions',
      'RuntimeHooks:',
      '- Trace each phase invocation and carry deterministic run identifier.',
      '- Persist phase payload snapshots for evidence-backed audit.',
      'BehavioralGuarantees:',
      requirements,
      `SuccessCriteria: ${input.request.successCriteria ?? 'Inferred from requirements and conformance tests.'}`,
    ].join('\n');

    return ok(artifact);
  }
}
