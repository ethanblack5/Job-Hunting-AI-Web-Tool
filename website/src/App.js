import { useState } from 'react';
import './App.css';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';

function App() {
  // Holds the full backend response (results + analytics + query echo),
  // shaped per docs/frontend-data-contract.md.
  const [searchResponse, setSearchResponse] = useState(null);

  return (
    <div className="App">
      {searchResponse ? (
        <ResultsPage
          searchResponse={searchResponse}
          setSearchResponse={setSearchResponse}
        />
      ) : (
        <HomePage setSearchResponse={setSearchResponse} />
      )}
    </div>
  );
}

export default App;
