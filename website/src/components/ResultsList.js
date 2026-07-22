import JobCard from './JobCard';

function ResultsList({ results }) {
  if (results.length === 0) {
    return (
      <div className="empty-state">
        <p>No matching jobs found. Try broadening your search criteria.</p>
      </div>
    );
  }

  return (
    <div className="results-list">
      {results.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}

export default ResultsList;
