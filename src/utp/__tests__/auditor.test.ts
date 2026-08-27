import test from 'node:test';
import assert from 'node:assert/strict';
import { runRealityAuditor } from '../phases/reality_auditor.js';

test('auditor discrepancy mapping is stable', async () => {
  const result = await runRealityAuditor({
    map: {
      interfaces: 'x',
      state: 'y',
      transitions: ['t1'],
      constraints: ['c1'],
      failureModes: ['f1'],
    },
    spec: {
      glossary: [{ term: 'Entity', definition: 'd' }],
      requirements: [{
        id: 'R1',
        givenWhenThen: 'g',
        preconditions: 'p',
        guarantees: 'g',
        observables: 'o',
        coversTransitions: ['not-t1'],
      }],
      nonFunctionalConstraints: ['n'],
      conformanceTests: [{ id: 'T1', validatesRequirements: ['R1'], procedure: 'p', expected: 'e' }],
    },
    artifact: {
      content: 'missing-marker',
      metadata: { targetDomain: 'x', targetEnvironment: 'y', generatedAt: new Date().toISOString() },
      buildHooks: [],
      runHooks: [],
    },
  });
  assert.equal(result.ok, true);
  if (result.ok) {
    assert.equal(result.value.discrepancies[0]?.id, 'D1');
  }
});
