import { describe, expect, it } from 'vitest';

import { createGreeting } from '../src/index.js';

describe('createGreeting', () => {
  it('creates a greeting with trimmed name', () => {
    expect(createGreeting({ name: ' Ada ' })).toBe('Hello, Ada!');
  });

  it('throws for missing name', () => {
    expect(() => createGreeting({ name: '   ' })).toThrowError(/Name is required/);
  });
});
