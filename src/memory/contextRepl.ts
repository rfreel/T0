import { ContextPatch } from './types.js';

export class ContextRepl {
  public apply(baseInstructions: string, patches: ContextPatch[]): string {
    return patches.reduce((instructions, patch) => {
      if (patch.operation === 'replace') {
        return patch.content;
      }
      return `${instructions}\n${patch.content}`;
    }, baseInstructions);
  }
}
