import { appendFile, writeFile } from 'node:fs/promises';
import { err, ok, Result } from '../types/result.js';
import { PipelineInput, pipelineInputSchema } from './models.js';
import { runDeconstructionist } from './phases/deconstructionist.js';
import { runNativeCreator } from './phases/native_creator.js';
import { runOntologist } from './phases/ontologist.js';
import { runRealityAuditor } from './phases/reality_auditor.js';
import { ensureDir, utcRunId, writeJsonDeterministic } from './utils/fs.js';
import { auditTrailMiddleware, determinismMiddleware, schemaValidationMiddleware } from './harness/middleware.js';
import { Harness } from './harness/toolRegistry.js';
import { createDefaultToolRegistry } from './tools.js';
import { loadAdapter } from './adapters/index.js';

export type PipelineRunOutput = {
  runDir: string;
};

const event = async (runDir: string, type: string, payload: Record<string, unknown>): Promise<void> => {
  await appendFile(`${runDir}/run.ndjson`, `${JSON.stringify({ ts: new Date().toISOString(), type, ...payload })}\n`, 'utf8');
};

export const run = async (
  sourceArtifact: string,
  sourceDomain: string,
  targetDomain: string,
  targetEnv: string,
  successCriteria?: string,
  outRoot = 'runs',
): Promise<Result<PipelineRunOutput, string>> => {
  const parsedInput = pipelineInputSchema.safeParse({
    sourceArtifact,
    sourceDomain,
    targetDomain,
    targetEnvironment: targetEnv,
    successCriteria,
  });
  if (!parsedInput.success) {
    return err(parsedInput.error.message);
  }
  const input: PipelineInput = parsedInput.data;

  const runDir = `${outRoot}/${utcRunId()}`;
  await ensureDir(runDir);
  await writeJsonDeterministic(`${runDir}/inputs.json`, input);
  await event(runDir, 'run_started', { sourceDomain, targetDomain });

  const registry = createDefaultToolRegistry();
  const adapterKind = (process.env.UTP_ADAPTER === 'autogen' ? 'autogen' : 'raw') as 'raw' | 'autogen';
  const adapter = loadAdapter(adapterKind, registry);
  await event(runDir, 'adapter_loaded', { kind: adapter.kind });

  const common = [schemaValidationMiddleware(), determinismMiddleware(), auditTrailMiddleware(`${runDir}/run.ndjson`)];

  const phase1 = new Harness(registry.subset(['extract_keywords']), common, 'phase1');
  await phase1.callTool({ toolName: 'extract_keywords', args: { text: input.sourceArtifact }, callId: '1' });
  const map = await runDeconstructionist(input);
  if (!map.ok) {
    return err(map.error);
  }
  await writeJsonDeterministic(`${runDir}/structural_logic_map.json`, map.value);

  const phase2 = new Harness(registry.subset(['transition_mapper']), common, 'phase2');
  await phase2.callTool({ toolName: 'transition_mapper', args: { transitions: map.value.transitions }, callId: '1' });
  const spec = await runOntologist(map.value);
  if (!spec.ok) {
    return err(spec.error);
  }
  await writeJsonDeterministic(`${runDir}/spec.json`, spec.value);

  const phase3 = new Harness(registry.subset(['artifact_renderer']), common, 'phase3');
  await phase3.callTool({ toolName: 'artifact_renderer', args: { lines: ['portable_layer=enabled'] }, callId: '1' });
  const artifact = await runNativeCreator({ request: input, spec: spec.value });
  if (!artifact.ok) {
    return err(artifact.error);
  }
  await writeFile(`${runDir}/target_artifact.txt`, artifact.value.content, 'utf8');
  await writeJsonDeterministic(`${runDir}/target_artifact.json`, artifact.value);

  const phase4 = new Harness(registry.subset(['evidence_reader']), common, 'phase4');
  await phase4.callTool({ toolName: 'evidence_reader', args: { path: `${runDir}/target_artifact.json` }, callId: '1' });
  const audit = await runRealityAuditor({ map: map.value, spec: spec.value, artifact: artifact.value, goldenMode: true });
  if (!audit.ok) {
    return err(audit.error);
  }
  await writeJsonDeterministic(`${runDir}/audit_report.json`, audit.value);
  await writeJsonDeterministic(`${runDir}/patch_instructions.json`, audit.value.patchInstructions);
  await event(runDir, 'run_completed', { discrepancies: audit.value.discrepancies.length });

  return ok({ runDir });
};

export const replayAudit = async (runDir: string): Promise<Result<string, string>> => {
  await event(runDir, 'replay_requested', {});
  return ok(`${runDir}/audit_report.json`);
};
