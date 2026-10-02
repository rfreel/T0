export type UtpInput = {
  sourceArtifact: string;
  originalSourceDomain: string;
  targetDomain: string;
  targetEnvironment: string;
  successCriteria?: string;
};

export type StructuralLogicMap = {
  Interfaces: string;
  State: string;
  Transitions: string;
  Constraints: string;
  FailureModes: string;
};

export type Requirement = {
  id: string;
  givenWhenThen: string;
  preconditions: string;
  guarantees: string;
  observables: string;
};

export type MediumAgnosticSpec = {
  Glossary: string;
  Requirements: Requirement[];
  NonFunctionalConstraints: string;
  ConformanceTests: string[];
};

export type AuditResult = {
  TestResults: string[];
  Discrepancies: string[];
  RootCauseHypotheses: string[];
  Severity: string;
};

export type UtpOutput = {
  STRUCTURAL_LOGIC_MAP: string;
  MEDIUM_AGNOSTIC_SPEC: string;
  TARGET_ARTIFACT: string;
  AUDIT_REPORT: string;
  PATCH_INSTRUCTIONS: string;
};
