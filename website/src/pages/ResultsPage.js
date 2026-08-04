import { useState } from 'react';
import ResultsList from '../components/ResultsList';
import ScoreGuide from '../components/ScoreGuide';
import SkillChart from '../components/SkillChart';
import { SCORE_BUCKETS } from '../scoreThresholds';

// Two-column layout per UI/UX spec: ranked cards left, skill-frequency
// chart + score guide right.

// Filter options built from the same tiers as the score guide, plus an
// "All matches" option with no cutoff. Ordered loosest to strictest so the
// list reads as progressively narrowing. Labels say "or better" because
// each option is a floor, not a band — "Good or better" includes strong
// matches too, unlike the bands shown in the score guide.
const FILTER_OPTIONS = [
  { key: 'all', label: 'All matches', min: 0 },
  ...SCORE_BUCKETS.filter((b) => b.min > 0)
    .slice()
    .sort((a, b) => a.min - b.min)
    .map((b) => ({
      key: b.key,
      label: `${b.label.replace(' match', '')} or better (${Math.round(b.min * 100)}%+)`,
      min: b.min,
    })),
];

function ResultsPage({ searchResponse, setSearchResponse }) {
  const [sortBy, setSortBy] = useState('score');
  const [minScoreKey, setMinScoreKey] = useState('all');
  const { query_echo, match_count, results, analytics } = searchResponse;

  const minScore = FILTER_OPTIONS.find((o) => o.key === minScoreKey)?.min ?? 0;

  // Sort toggle is client-side for now — open question in the data contract
  // (§3, P2) whether this becomes a backend request instead.
  const sorted = [...results].sort((a, b) => {
    if (sortBy === 'recent') {
      // Null dates sort last.
      const da = a.date_listed ? new Date(a.date_listed) : 0;
      const db = b.date_listed ? new Date(b.date_listed) : 0;
      return db - da;
    }
    return b.score - a.score;
  });

  // Threshold filter. Results with a null score (retrieval not yet
  // returning a value for that item) are kept rather than hidden, since
  // hiding them would look like a bug rather than a low-scoring match.
  const filtered = sorted.filter((job) => job.score == null || job.score >= minScore);

  const activeCriteria = [
    query_echo.job_title,
    ...(query_echo.skills ?? []),
    query_echo.location,
    query_echo.experience_level,
  ].filter(Boolean);

  return (
    <div className="results-page">
      <div className="filter-bar">
        <div className="filter-criteria">
          {activeCriteria.map((c) => (
            <span key={c} className="criteria-chip">
              {c}
            </span>
          ))}
          <span className="match-count">
            {filtered.length === results.length
              ? `${match_count} matches`
              : `${filtered.length} of ${match_count} matches`}
          </span>
        </div>
        <div className="filter-actions">
          <select
            className="min-score-select"
            value={minScoreKey}
            onChange={(e) => setMinScoreKey(e.target.value)}
            aria-label="Minimum match score"
          >
            {FILTER_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>
                {o.label}
              </option>
            ))}
          </select>
          <button
            className={sortBy === 'score' ? 'sort-btn active' : 'sort-btn'}
            onClick={() => setSortBy('score')}
          >
            Score
          </button>
          <button
            className={sortBy === 'recent' ? 'sort-btn active' : 'sort-btn'}
            onClick={() => setSortBy('recent')}
          >
            Recent
          </button>
          <button className="btn-secondary" onClick={() => setSearchResponse(null)}>
            New Search
          </button>
        </div>
      </div>

      <div className="results-grid">
        <main>
          <ResultsList results={filtered} />
        </main>
        <div className="results-sidebar">
          <SkillChart analytics={analytics} />
          <ScoreGuide />
        </div>
      </div>
    </div>
  );
}

export default ResultsPage;
