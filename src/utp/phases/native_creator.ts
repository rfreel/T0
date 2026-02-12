import { err, ok, Result } from '../../types/result.js';
import { MediumAgnosticSpec, PipelineInput, TargetArtifact, targetArtifactSchema } from '../models.js';

export const requiredTools = () => ['artifact_renderer'];

export type NativeCreatorInput = {
  request: PipelineInput;
  spec: MediumAgnosticSpec;
};

export const runNativeCreator = async (input: NativeCreatorInput): Promise<Result<TargetArtifact, string>> => {
  const candidate = {
    content: [
      `target_domain=${input.request.targetDomain}`,
      `target_environment=${input.request.targetEnvironment}`,
      `requirements=${input.spec.requirements.length}`,
      'portable_layer=enabled',
    ].join('\n'),
    metadata: {
      targetDomain: input.request.targetDomain,
      targetEnvironment: input.request.targetEnvironment,
      generatedAt: new Date().toISOString(),
    },
    buildHooks: ['pnpm typecheck', 'pnpm build'],
    runHooks: ['pnpm dev', 'pnpm utp:run --source examples/utp/prompt-stack/inputs/source.txt --source-domain prompt --target-domain prompt --target-env local'],
  };

  const valid = targetArtifactSchema.safeParse(candidate);
  if (!valid.success) {
    return err(valid.error.message);
  }
  return ok(valid.data);
};
