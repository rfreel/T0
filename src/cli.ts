#!/usr/bin/env node
import process from 'node:process';

import { createGreeting } from './index.js';

function parseName(argv: string[]): string {
  const nameFlagIndex = argv.findIndex((arg) => arg === '--name');
  if (nameFlagIndex !== -1 && argv[nameFlagIndex + 1]) {
    return argv[nameFlagIndex + 1];
  }
  const directName = argv.slice(2)[0];
  return directName ?? '';
}

function main(): void {
  try {
    const name = parseName(process.argv);
    const message = createGreeting({ name });
    // eslint-disable-next-line no-console
    console.log(message);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    // eslint-disable-next-line no-console
    console.error(`Error: ${message}`);
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
