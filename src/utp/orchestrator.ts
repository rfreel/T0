import { err, ok, Result } from '../types/result.js';
import { AbstractSpecifierAgent } from './abstractSpecifierAgent.js';
import { DomainSpecialistAgent } from './domainSpecialistAgent.js';
import { StructuralAnalystAgent } from './structuralAnalystAgent.js';
import { UtpInput, UtpOutput } from './types.js';
import { VarianceDetectorAgent } from './varianceDetectorAgent.js';

const formatRequirements = (requirements: { id: string; givenWhenThen: string; preconditions: string; guarantees: string; observables: string }[]): string =>
  requirements
    .map((requirement) => [
      `${requirement.id}:`,
      `Given/When/Then: ${requirement.givenWhenThen}`,
      `Preconditions: ${requirement.preconditions}`,
      `Guarantees: ${requirement.guarantees}`,
      `Observables: ${requirement.observables}`,
    ].join('\n'))
    .join('\n\n');

const formatPatchInstructions = (discrepancies: string[]): string => {
  if (discrepancies.length === 0) {
    return '1) No edits required.\n- file/module: none\n- change: none\n- expected effect: all tests remain passing\n- evidence: rerun T1-T4 with unchanged outputs';
  }

  return discrepancies
    .map((discrepancy, index) => [
      `${index + 1}) file/module: src/utp/* relevant phase module`,
      `- change: address ${discrepancy}`,
      '- expected effect: restores conformance for violated requirement and associated test.',
      '- evidence: updated test results showing pass for impacted test IDs.',
    ].join('\n'))
    .join('\n');
};

export class UtpOrchestrator {
  private readonly structuralAnalyst = new StructuralAnalystAgent();
  private readonly abstractSpecifier = new AbstractSpecifierAgent();
  private readonly domainSpecialist = new DomainSpecialistAgent();
  private readonly varianceDetector = new VarianceDetectorAgent();

  public async execute(input: UtpInput): Promise<Result<UtpOutput, string>> {
    const structural = await this.structuralAnalyst.call(input);
    if (!structural.ok) {
      return err(structural.error);
    }

    const spec = await this.abstractSpecifier.call(structural.value);
    if (!spec.ok) {
      return err(spec.error);
    }

    const artifact = await this.domainSpecialist.call({ request: input, spec: spec.value });
    if (!artifact.ok) {
      return err(artifact.error);
    }

    const audit = await this.varianceDetector.call({ map: structural.value, spec: spec.value, artifact: artifact.value });
    if (!audit.ok) {
      return err(audit.error);
    }

    return ok({
      STRUCTURAL_LOGIC_MAP: [
        `Interfaces:\n${structural.value.Interfaces}`,
        `State:\n${structural.value.State}`,
        `Transitions:\n${structural.value.Transitions}`,
        `Constraints:\n${structural.value.Constraints}`,
        `FailureModes:\n${structural.value.FailureModes}`,
      ].join('\n\n'),
      MEDIUM_AGNOSTIC_SPEC: [
        `Glossary:\n${spec.value.Glossary}`,
        `Requirements:\n${formatRequirements(spec.value.Requirements)}`,
        `NonFunctionalConstraints:\n${spec.value.NonFunctionalConstraints}`,
        `ConformanceTests:\n${spec.value.ConformanceTests.join('\n')}`,
      ].join('\n\n'),
      TARGET_ARTIFACT: artifact.value,
      AUDIT_REPORT: [
        `TestResults:\n${audit.value.TestResults.join('\n')}`,
        `Discrepancies:\n${audit.value.Discrepancies.length === 0 ? 'none' : audit.value.Discrepancies.join('\n')}`,
        `RootCauseHypotheses:\n${audit.value.RootCauseHypotheses.join('\n')}`,
        `Severity:\n${audit.value.Severity}`,
      ].join('\n\n'),
      PATCH_INSTRUCTIONS: formatPatchInstructions(audit.value.Discrepancies),
    });
  }
}
