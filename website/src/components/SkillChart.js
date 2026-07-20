// Skill-frequency bar chart. PR3 task — depends on Jawwad's analytics
// payload (docs/frontend-data-contract.md §5). Renders a placeholder
// until that payload format is confirmed.
function SkillChart({ analytics }) {
  const skills = analytics?.skill_frequency ?? [];

  if (skills.length === 0) {
    return (
      <div className="chart-placeholder">
        <h3>Skill Frequency</h3>
        <p>Chart coming in PR3 (pending analytics payload).</p>
      </div>
    );
  }

  const maxCount = Math.max(...skills.map((s) => s.count));

  return (
    <div className="chart-placeholder">
      <h3>Skill Frequency</h3>
      <div className="skill-chart-bars">
        {skills.map((s) => (
          <div key={s.skill} className="skill-chart-row" title={`${s.count} matched postings`}>
            <span className="skill-chart-label">{s.skill}</span>
            <div className="skill-chart-track">
              <div
                className="skill-chart-fill"
                style={{ width: `${(s.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="skill-chart-count">{s.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SkillChart;