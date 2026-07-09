function JobCard({ job }) {
  return (
    <div>
      <h3>{job.title}</h3>
      <p>{job.company}</p>
      <p>{job.location}</p>
      <p>{job.salary}</p>
      <p>{job.type}</p>
      <p>{job.date}</p>
      <p>{job.description}</p>
      <p>Match Score: {job.score}</p>
      <p>Skills: {job.skills.join(', ')}</p>
      <a href={job.link} target="_blank" rel="noreferrer">Apply</a>
    </div>
  );
}

export default JobCard;