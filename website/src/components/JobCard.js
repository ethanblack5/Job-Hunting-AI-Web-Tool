// Renders one ranked job result per the UI/UX spec:
// score ring, role, company, location, salary, role type, listing date,
// description, skill tags, apply link.
// Field names per docs/frontend-data-contract.md. salary, company, location,
// role_type, and date_listed can be null and are hidden when absent.

function ScoreRing({ score }) {
  // score: 0.0–1.0 similarity (assumed pending Chloe's confirmation on
  // score direction — see data contract §6).
  const pct = Math.round(score * 100);
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const filled = circumference * score;

  return (
    <div className="score-ring" title={`Match score: ${pct}%`}>
      <svg width="64" height="64" viewBox="0 0 64 64" role="img" aria-label={`Match score ${pct} percent`}>
        <circle className="score-ring-track" cx="32" cy="32" r={radius} strokeWidth="6" fill="none" />
        <circle
          className="score-ring-fill"
          cx="32"
          cy="32"
          r={radius}
          strokeWidth="6"
          fill="none"
          strokeDasharray={`${filled} ${circumference - filled}`}
          strokeDashoffset={circumference / 4}
          strokeLinecap="round"
        />
      </svg>
      <span className="score-ring-label">{pct}%</span>
    </div>
  );
}

function daysAgo(isoDate) {
  const days = Math.floor((Date.now() - new Date(isoDate)) / 86400000);
  if (days <= 0) return 'Listed today';
  if (days === 1) return 'Listed 1 day ago';
  return `Listed ${days} days ago`;
}

function JobCard({ job }) {
  return (
    <article className="job-card">
      <div className="job-card-header">
        <ScoreRing score={job.score} />
        <div className="job-card-heading">
          <h3 className="job-title">{job.title}</h3>
          <p className="job-company">{job.company ?? 'Company not listed'}</p>
          <div className="job-meta">
            {job.location && <span>{job.location}</span>}
            {job.role_type && <span className="role-badge">{job.role_type}</span>}
            {job.date_listed && <span>{daysAgo(job.date_listed)}</span>}
          </div>
        </div>
      </div>

      {job.salary && <p className="job-salary">{job.salary}</p>}

      <p className="job-description">{job.description}</p>

      {job.skills.length > 0 && (
        <div className="job-skills">
          {job.skills.map((skill) => (
            <span key={skill} className="skill-tag">
              {skill}
            </span>
          ))}
        </div>
      )}

      <a className="apply-link" href={job.apply_url} target="_blank" rel="noreferrer">
        Apply
      </a>
    </article>
  );
}

export default JobCard;
