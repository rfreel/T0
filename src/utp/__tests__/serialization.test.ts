import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { writeJsonDeterministic } from '../utils/fs.js';

test('artifact serialization preserves JSON semantics and deterministic nested ordering', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'utp-json-'));
  try {
    const path = join(directory, 'inputs.json');
    await writeJsonDeterministic(path, {
      successCriteria: undefined,
      sourceArtifact: 'x',
      nested: { z: 2, a: 1, absent: undefined },
      array: [undefined, { z: 2, a: 1 }],
      date: new Date('2026-01-01T00:00:00.000Z'),
    });
    const raw = await readFile(path, 'utf8');
    assert.equal(raw, '{"array":[null,{"a":1,"z":2}],"date":"2026-01-01T00:00:00.000Z","nested":{"a":1,"z":2},"sourceArtifact":"x"}\n');
    assert.equal(JSON.parse(raw).sourceArtifact, 'x');
    await assert.rejects(writeJsonDeterministic(path, undefined), TypeError);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
