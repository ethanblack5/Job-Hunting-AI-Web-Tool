import { useState } from 'react';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';

function App() {
  const [results, setResults] = useState(null);

  return (
    <div className="App">
      {results ? (
        <ResultsPage results={results} setResults={setResults} />
      ) : (
        <HomePage setResults={setResults} />
      )}
    </div>
  );
}

export default App;