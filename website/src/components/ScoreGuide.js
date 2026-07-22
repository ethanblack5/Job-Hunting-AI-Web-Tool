// Match score legend per UI/UX spec (Figure 7).
// Thresholds are PLACEHOLDERS — final buckets come from Jawwad's ranking
// evaluation (data contract §6, P2). Update BUCKETS when confirmed.
const BUCKETS = [
  { label: 'Strong match', range: '80–100%', className: 'bucket-strong' },
  { label: 'Good match', range: '60–79%', className: 'bucket-good' },
  { label: 'Partial match', range: '40–59%', className: 'bucket-partial' },
  { label: 'Weak match', range: 'Below 40%', className: 'bucket-weak' },
];

function ScoreGuide() {
  return (
    <aside className="score-guide">
      <h3>Match Score Guide</h3>
      <ul>
        {BUCKETS.map((b) => (
          <li key={b.label}>
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
