// Shared match-score tiers. Used by ScoreGuide.js (legend) and
// ResultsPage.js (minimum-score filter) so both stay in sync.
//
// Thresholds are PLACEHOLDERS — final buckets come from Jawwad's ranking
// evaluation (data contract §6, P2). Update the `min` values here once
// confirmed; both the guide and the filter pick it up automatically.

export const SCORE_BUCKETS = [
  { key: 'strong', label: 'Strong match', range: '80–100%', min: 0.8, className: 'bucket-strong' },
  { key: 'good', label: 'Good match', range: '60–79%', min: 0.6, className: 'bucket-good' },
  { key: 'partial', label: 'Partial match', range: '40–59%', min: 0.4, className: 'bucket-partial' },
  { key: 'weak', label: 'Weak match', range: 'Below 40%', min: 0, className: 'bucket-weak' },
];

// Returns the bucket a score falls into, or null when there's no score.
// Sorts by threshold rather than relying on SCORE_BUCKETS' declared order,
// so reordering the list above can't silently break this.
export function bucketForScore(score) {
  if (score == null || Number.isNaN(score)) return null;
  return (
    [...SCORE_BUCKETS]
      .sort((a, b) => b.min - a.min)
      .find((b) => score >= b.min) ?? null
  );
}
