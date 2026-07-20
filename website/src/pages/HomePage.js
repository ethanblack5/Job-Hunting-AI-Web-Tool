import SearchForm from '../components/SearchForm';

const STEPS = [
  {
    n: '01',
    title: 'Tell it what you want',
    body: 'Role, skills, location, experience level.',
  },
  {
    n: '02',
    title: 'It reads for meaning',
    body: 'Related roles surface even under unfamiliar titles.',
  },
  {
    n: '03',
    title: 'See ranked results',
    body: 'Every match scored, with common skills charted.',
  },
];

function HomePage({ setSearchResponse }) {
  return (
    <div className="home-page">
      <header className="home-brand">
        <span className="home-brand-mark" aria-hidden="true" />
        <h1 className="home-brand-name">Job Hunting AI Web Tool</h1>
      </header>

      <div className="home-grid">
        <div className="home-copy">
          <p className="home-eyebrow">Semantic job search</p>

          <p className="home-headline">
            Remote jobs that match
            <br />
            <span className="home-h1-accent">what you actually do</span>
          </p>

          <p className="home-tagline">
            Describe the role you want in normal language. The search
            understands what you mean and finds postings that fit, however
            they're worded.
          </p>

          <ol className="home-steps">
            {STEPS.map((s) => (
              <li key={s.n} className="home-step">
                <span className="home-step-n">{s.n}</span>
                <div className="home-step-text">
                  <h2 className="home-step-title">{s.title}</h2>
                  <p className="home-step-body">{s.body}</p>
                </div>
              </li>
            ))}
          </ol>

          <p className="home-footnote">
            Built on sentence-transformers + ChromaDB · postings from RemoteOK
          </p>
        </div>

        <div className="home-form-col">
          <SearchForm setSearchResponse={setSearchResponse} />
        </div>
      </div>
    </div>
  );
}

export default HomePage;