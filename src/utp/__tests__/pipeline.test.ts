import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { run } from '../pipeline.js';

test('pipeline artifacts are written', async () => {
  const out = await mkdtemp(`${tmpdir()}/utp-`);
  const result = await run('a\nwhen b', 'source', 'target', 'env', undefined, out);
  assert.equal(result.ok, true);
  if (result.ok) {
    const log = await readFile(`${result.value.runDir}/run.ndjson`, 'utf8');
    assert.ok(log.includes('run_started'));
  }
});
