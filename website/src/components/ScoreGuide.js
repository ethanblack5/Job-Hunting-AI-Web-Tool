import { SCORE_BUCKETS } from '../scoreThresholds';

// Match score legend per UI/UX spec (Figure 7).
// Bucket thresholds live in scoreThresholds.js so the guide and the
// results filter (ResultsPage.js) stay in sync.

function ScoreGuide() {
  return (
    <aside className="score-guide">
      <h3>Match Score Guide</h3>
      <ul>
        {SCORE_BUCKETS.map((b) => (
          <li key={b.key}>
            <span className={`bucket-dot ${b.className}`} aria-hidden="true" />
            <span className="bucket-label">{b.label}</span>
            <span className="bucket-range">{b.range}</span>
          </li>
        ))}
      </ul>
      <p className="score-guide-note">
        Scores estimate how closely a posting matches your search. They are a
        guide, not a guarantee of fit.
      </p>
    </aside>
  );
}

export default ScoreGuide;
