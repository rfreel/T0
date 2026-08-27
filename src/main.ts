import { UtpOrchestrator } from './utp/orchestrator.js';

const main = async (): Promise<void> => {
  const orchestrator = new UtpOrchestrator();

  const run = await orchestrator.execute({
    sourceArtifact: `Implement a four-phase transpilation protocol with strict section outputs and conformance auditing.`,
    originalSourceDomain: 'instructional text',
    targetDomain: 'TypeScript callable-agent pipeline',
    targetEnvironment: 'Node.js 20+, strict TypeScript, CI-gated repository workflow',
    successCriteria: 'All conformance tests pass and discrepancies are empty.',
  });

  if (!run.ok) {
    process.stderr.write(`${run.error}\n`);
    process.exitCode = 1;
    return;
  }

  const sections: Array<keyof typeof run.value> = [
    'STRUCTURAL_LOGIC_MAP',
    'MEDIUM_AGNOSTIC_SPEC',
    'TARGET_ARTIFACT',
    'AUDIT_REPORT',
    'PATCH_INSTRUCTIONS',
  ];

  for (const section of sections) {
    process.stdout.write(`${section}\n${run.value[section]}\n\n`);
  }
};

void main();
