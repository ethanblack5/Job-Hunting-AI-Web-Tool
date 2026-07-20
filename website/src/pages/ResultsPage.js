import { useState } from 'react';
import ResultsList from '../components/ResultsList';
import ScoreGuide from '../components/ScoreGuide';
import SkillChart from '../components/SkillChart';

// Two-column layout per UI/UX spec: ranked cards left, skill-frequency
// chart + score guide right.

function ResultsPage({ searchResponse, setSearchResponse }) {
  const [sortBy, setSortBy] = useState('score');
  const { query_echo, match_count, results, analytics } = searchResponse;

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
          <span className="match-count">{match_count} matches</span>
        </div>
        <div className="filter-actions">
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
          <ResultsList results={sorted} />
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