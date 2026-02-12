export const computeDriftScore = (baseline: string, candidate: string): number => {
  const baselineTokens = new Set(baseline.toLowerCase().split(/\W+/).filter(Boolean));
  const candidateTokens = new Set(candidate.toLowerCase().split(/\W+/).filter(Boolean));

  if (baselineTokens.size === 0 && candidateTokens.size === 0) {
    return 0;
  }

  let intersection = 0;
  for (const token of baselineTokens) {
    if (candidateTokens.has(token)) {
      intersection += 1;
    }
  }

  const union = baselineTokens.size + candidateTokens.size - intersection;
  const jaccard = union === 0 ? 1 : intersection / union;
  return Number((1 - jaccard).toFixed(4));
};

export const approximateTokenCount = (value: string): number => Math.ceil(value.length / 4);
