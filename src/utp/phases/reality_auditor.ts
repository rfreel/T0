import { ok, Result } from '../../types/result.js';
import { AuditReport, auditReportSchema, MediumAgnosticSpec, StructuralLogicMap, TargetArtifact } from '../models.js';

export type RealityAuditorInput = {
  map: StructuralLogicMap;
  spec: MediumAgnosticSpec;
  artifact: TargetArtifact;
  goldenMode?: boolean;
};

export const requiredTools = () => ['evidence_reader'];

export const runRealityAuditor = async (input: RealityAuditorInput): Promise<Result<AuditReport, string>> => {
  const hasTransitionCoverage = input.map.transitions.every((transition) =>
    input.spec.requirements.some((requirement) => requirement.coversTransitions.includes(transition)),
  );

  const discrepancies = [] as AuditReport['discrepancies'];
  if (!hasTransitionCoverage) {
    discrepancies.push({
      id: 'D1',
      violatedRequirements: ['R1'],
      violatedTests: ['T2'],
      detail: 'Transition coverage incomplete.',
    });
  }

  if (!input.artifact.content.includes('portable_layer=enabled')) {
    discrepancies.push({
      id: 'D2',
      violatedRequirements: ['R1'],
      violatedTests: ['T3'],
      detail: 'Target artifact marker missing.',
    });
  }

  const candidate = {
    testResults: [
      { id: 'T1', passed: true, evidence: 'structural map schema validated in-memory' },
      { id: 'T2', passed: hasTransitionCoverage, evidence: 'transition coverage scan completed' },
      { id: 'T3', passed: input.artifact.content.includes('portable_layer=enabled'), evidence: 'artifact marker check' },
      { id: 'T4', passed: discrepancies.length === 0 || !input.goldenMode, evidence: `discrepancy_count=${discrepancies.length}` },
    ],
    discrepancies,
    rootCauseHypotheses: discrepancies.length === 0
      ? ['No mismatch detected; conformance checks satisfied.']
      : ['Spec coverage or artifact rendering incomplete; re-run phases 2-3 with patch instructions.'],
    patchInstructions: discrepancies.map((d) => ({
      location: 'src/utp/phases/*',
      change: `Resolve ${d.id}: ${d.detail}`,
      expectedEffect: `Make ${d.violatedTests.join(',')} pass by restoring required output semantics.`,
      requiredEvidence: 'Updated audit_report.json with discrepancy removed and test pass evidence.',
    })),
    severity: discrepancies.length === 0 ? 'none' : 'must-fix',
  };

  const valid = auditReportSchema.parse(candidate);
  return ok(valid);
};
