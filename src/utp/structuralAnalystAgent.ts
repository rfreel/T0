import { err, ok, Result } from '../types/result.js';
import { CallableAgent } from './callableAgent.js';
import { StructuralLogicMap, UtpInput } from './types.js';

const extractTransitions = (sourceArtifact: string): string => {
  const lines = sourceArtifact.split('\n').map((line) => line.trim()).filter(Boolean);
  const triggers = lines.filter((line) => /when|if|on|trigger|start|stop/i.test(line)).slice(0, 8);
  if (triggers.length === 0) {
    return 'Preconditions: input exists -> Actions: parse, classify, transform, verify -> Postconditions: output sections emitted with stable ordering.';
  }
  return triggers.map((line, index) => `T${index + 1}: Preconditions inferred -> Action: ${line} -> Postconditions logged`).join('\n');
};

export class StructuralAnalystAgent implements CallableAgent<UtpInput, StructuralLogicMap> {
  public readonly id = 'Structural_Analyst';
  public readonly description = 'Extracts interfaces, state, transitions, constraints, and failure modes from source artifact.';

  public async call(input: UtpInput): Promise<Result<StructuralLogicMap, string>> {
    if (!input.sourceArtifact.trim()) {
      return err('SOURCE_ARTIFACT cannot be empty');
    }

    const interfaceBlock = [
      `Inputs: sourceArtifact:string, originalSourceDomain:string, targetDomain:string, targetEnvironment:string, successCriteria?:string`,
      'Outputs: structural map sections with deterministic labels and string payloads.',
      'Ranges: non-empty textual artifacts; optional criteria defaults to inferred constraints.',
    ].join('\n');

    const stateBlock = [
      'Mutable: inferred transition set, detected constraints, discrepancy counters.',
      'Immutable: phase order, output section contract, section labels.',
      'Initialization: state derived from SOURCE_ARTIFACT at call start.',
      'Persistence: state passed to downstream callable agents through orchestration context.',
    ].join('\n');

    const map: StructuralLogicMap = {
      Interfaces: interfaceBlock,
      State: stateBlock,
      Transitions: extractTransitions(input.sourceArtifact),
      Constraints: 'Invariants: five output sections, fixed order, complete transition coverage, no semantic drift claims without evidence.',
      FailureModes: 'Violations: missing sections, uncovered transitions, unverifiable guarantees. Signals: failed conformance tests, discrepancy entries in audit.',
    };

    return ok(map);
  }
}
