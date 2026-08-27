#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { run, replayAudit } from './pipeline.js';

const arg = (name: string): string | undefined => {
  const idx = process.argv.indexOf(name);
  return idx >= 0 ? process.argv[idx + 1] : undefined;
};

const command = process.argv[2];

const execute = async (): Promise<void> => {
  if (command === 'run') {
    const sourcePath = arg('--source');
    const sourceDomain = arg('--source-domain');
    const targetDomain = arg('--target-domain');
    const targetEnv = arg('--target-env');
    const out = arg('--out') ?? 'runs';
    if (!sourcePath || !sourceDomain || !targetDomain || !targetEnv) {
      process.stderr.write('missing required args for run\n');
      process.exitCode = 1;
      return;
    }
    const sourceArtifact = await readFile(sourcePath, 'utf8');
    const result = await run(sourceArtifact, sourceDomain, targetDomain, targetEnv, undefined, out);
    if (!result.ok) {
      process.stderr.write(`${result.error}\n`);
      process.exitCode = 1;
      return;
    }
    process.stdout.write(`${result.value.runDir}\n`);
    return;
  }

  if (command === 'audit' || command === 'replay') {
    const runDir = arg('--run');
    if (!runDir) {
      process.stderr.write('missing --run\n');
      process.exitCode = 1;
      return;
    }
    const result = await replayAudit(runDir);
    if (!result.ok) {
      process.stderr.write(`${result.error}\n`);
      process.exitCode = 1;
      return;
    }
    process.stdout.write(`${result.value}\n`);
    return;
  }

  process.stderr.write('usage: utp <run|audit|replay> ...\n');
  process.exitCode = 1;
};

void execute();
