import test from 'node:test';
import assert from 'node:assert/strict';
import { z } from 'zod';
import { ToolRegistry, Harness } from '../harness/toolRegistry.js';
import { determinismMiddleware } from '../harness/middleware.js';

test('schema validation rejects bad tool args', async () => {
  const registry = new ToolRegistry();
  registry.register({
    name: 'adder',
    description: 'adds',
    jsonSchema: z.object({ a: z.number(), b: z.number() }).strict(),
    callable: async ({ a, b }) => a + b,
  });

  const harness = new Harness(registry, [determinismMiddleware()], 'test');
  const result = await harness.callTool({ toolName: 'adder', args: { a: 1, b: 'x' }, callId: '1' });
  assert.equal(result.ok, false);
});
