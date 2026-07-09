import ResultsList from '../components/ResultsList';

function ResultsPage({ results, setResults }) {
  return (
    <div>
      <button onClick={() => setResults(null)}>New Search</button>
      <h2>Search Results</h2>
      <ResultsList results={results} />
    </div>
  );
}

export default ResultsPage;