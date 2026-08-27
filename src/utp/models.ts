import { z } from 'zod';

export const structuralLogicMapSchema = z.object({
  interfaces: z.string().min(1),
  state: z.string().min(1),
  transitions: z.array(z.string().min(1)).min(1),
  constraints: z.array(z.string().min(1)).min(1),
  failureModes: z.array(z.string().min(1)).min(1),
}).strict();

export const requirementSchema = z.object({
  id: z.string().regex(/^R\d+$/),
  givenWhenThen: z.string().min(1),
  preconditions: z.string().min(1),
  guarantees: z.string().min(1),
  observables: z.string().min(1),
  coversTransitions: z.array(z.string().min(1)).min(1),
}).strict();

export const conformanceTestSchema = z.object({
  id: z.string().regex(/^T\d+$/),
  validatesRequirements: z.array(z.string().regex(/^R\d+$/)).min(1),
  procedure: z.string().min(1),
  expected: z.string().min(1),
}).strict();

export const mediumAgnosticSpecSchema = z.object({
  glossary: z.array(z.object({ term: z.string().min(1), definition: z.string().min(1) }).strict()).min(1),
  requirements: z.array(requirementSchema).min(1),
  nonFunctionalConstraints: z.array(z.string().min(1)).min(1),
  conformanceTests: z.array(conformanceTestSchema).min(1),
}).strict();

export const targetArtifactSchema = z.object({
  content: z.string().min(1),
  metadata: z.object({
    targetDomain: z.string().min(1),
    targetEnvironment: z.string().min(1),
    generatedAt: z.string().datetime(),
  }).strict(),
  buildHooks: z.array(z.string().min(1)),
  runHooks: z.array(z.string().min(1)),
}).strict();

export const discrepancySchema = z.object({
  id: z.string().regex(/^D\d+$/),
  violatedRequirements: z.array(z.string().regex(/^R\d+$/)).min(1),
  violatedTests: z.array(z.string().regex(/^T\d+$/)).min(1),
  detail: z.string().min(1),
}).strict();

export const patchInstructionSchema = z.object({
  location: z.string().min(1),
  change: z.string().min(1),
  expectedEffect: z.string().min(1),
  requiredEvidence: z.string().min(1),
}).strict();

export const auditReportSchema = z.object({
  testResults: z.array(z.object({ id: z.string().regex(/^T\d+$/), passed: z.boolean(), evidence: z.string().min(1) }).strict()).min(1),
  discrepancies: z.array(discrepancySchema),
  rootCauseHypotheses: z.array(z.string().min(1)).min(1),
  patchInstructions: z.array(patchInstructionSchema),
  severity: z.enum(['none', 'must-fix', 'optional']),
}).strict();

export const pipelineInputSchema = z.object({
  sourceArtifact: z.string().min(1),
  sourceDomain: z.string().min(1),
  targetDomain: z.string().min(1),
  targetEnvironment: z.string().min(1),
  successCriteria: z.string().optional(),
}).strict();

export type StructuralLogicMap = z.infer<typeof structuralLogicMapSchema>;
export type MediumAgnosticSpec = z.infer<typeof mediumAgnosticSpecSchema>;
export type TargetArtifact = z.infer<typeof targetArtifactSchema>;
export type AuditReport = z.infer<typeof auditReportSchema>;
export type PipelineInput = z.infer<typeof pipelineInputSchema>;

export const exportSchemas = () => ({
  structuralLogicMap: structuralLogicMapSchema,
  mediumAgnosticSpec: mediumAgnosticSpecSchema,
  targetArtifact: targetArtifactSchema,
  auditReport: auditReportSchema,
  pipelineInput: pipelineInputSchema,
});
