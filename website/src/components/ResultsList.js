import JobCard from './JobCard';

function ResultsList({ results }) {
  return (
    <div>
      {results.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}

export default ResultsList;