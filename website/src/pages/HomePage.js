import SearchForm from '../components/SearchForm';

function HomePage({ setResults }) {
  return (
    <div>
      <h1>Job Hunting AI Web Tool</h1>
      <SearchForm setResults={setResults} />
    </div>
  );
}

export default HomePage;