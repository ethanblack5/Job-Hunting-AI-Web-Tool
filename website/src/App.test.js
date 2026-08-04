import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

const VALID_SEARCH_RESPONSE = {
  query_echo: {
    job_title: '',
    skills: [],
    location: 'remote',
    experience_level: '',
  },
  match_count: 1,
  results: [
    {
      id: 'remoteok:1',
      score: null,
      title: 'Backend Engineer',
      company: 'Acme',
      location: 'Remote (US)',
      salary: null,
      role_type: null,
      date_listed: '2026-07-20',
      description: 'Test description.',
      skills: ['python'],
      apply_url: 'https://example.com',
    },
  ],
  analytics: { skill_frequency: [{ skill: 'python', count: 1 }] },
};

const MIXED_SCORE_RESPONSE = {
  query_echo: {
    job_title: 'engineer',
    skills: [],
    location: 'remote',
    experience_level: '',
  },
  match_count: 3,
  results: [
    {
      id: 'remoteok:1',
      score: 0.92,
      title: 'Strong Match Role',
      company: 'Acme',
      location: 'Remote (US)',
      salary: null,
      role_type: null,
      date_listed: '2026-07-20',
      description: 'Test description.',
      skills: ['python'],
      apply_url: 'https://example.com',
    },
    {
      id: 'remoteok:2',
      score: 0.5,
      title: 'Partial Match Role',
      company: 'Acme',
      location: 'Remote (US)',
      salary: null,
      role_type: null,
      date_listed: '2026-07-19',
      description: 'Test description.',
      skills: ['python'],
      apply_url: 'https://example.com',
    },
    {
      id: 'remoteok:3',
      score: 0.2,
      title: 'Weak Match Role',
      company: 'Acme',
      location: 'Remote (US)',
      salary: null,
      role_type: null,
      date_listed: '2026-07-18',
      description: 'Test description.',
      skills: ['python'],
      apply_url: 'https://example.com',
    },
  ],
  analytics: { skill_frequency: [{ skill: 'python', count: 3 }] },
};

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders the search form on load', () => {
  render(<App />);
  expect(screen.getByText(/Job Hunting AI Web Tool/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Job Title/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Search Jobs/i })).toBeInTheDocument();
});

test('shows a loading state while the search is in flight', async () => {
  let resolveFetch;
  global.fetch.mockReturnValue(
    new Promise((resolve) => {
      resolveFetch = resolve;
    })
  );

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  const button = await screen.findByRole('button', { name: /Searching/i });
  expect(button).toBeDisabled();

  // Let the pending fetch resolve so the async state update inside
  // handleSubmit isn't left dangling after the test finishes.
  resolveFetch({
    ok: true,
    json: async () => VALID_SEARCH_RESPONSE,
  });
  await waitFor(() =>
    expect(screen.getByRole('button', { name: /New Search/i })).toBeInTheDocument()
  );
});

test('shows results page after a successful search', async () => {
  global.fetch.mockResolvedValue({
    ok: true,
    json: async () => VALID_SEARCH_RESPONSE,
  });

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  expect(await screen.findByText(/1 matches/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /New Search/i })).toBeInTheDocument();
});

test('shows an error message when the backend is unreachable', async () => {
  global.fetch.mockRejectedValue(new TypeError('Failed to fetch'));

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  expect(
    await screen.findByText(/can't reach the server/i)
  ).toBeInTheDocument();
  // Should stay on the search form, not navigate to results.
  expect(screen.getByRole('button', { name: /Search Jobs/i })).toBeInTheDocument();
});

test('shows the backend-provided error message on a non-OK response', async () => {
  global.fetch.mockResolvedValue({
    ok: false,
    status: 400,
    json: async () => ({ detail: 'Invalid search criteria.' }),
  });

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  expect(await screen.findByText(/Invalid search criteria\./i)).toBeInTheDocument();
});

test('dismissing the error clears it', async () => {
  global.fetch.mockRejectedValue(new TypeError('Failed to fetch'));

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  await screen.findByText(/can't reach the server/i);
  fireEvent.click(screen.getByRole('button', { name: /Dismiss error/i }));

  expect(screen.queryByText(/can't reach the server/i)).not.toBeInTheDocument();
});

test('minimum score filter hides results below the chosen threshold', async () => {
  global.fetch.mockResolvedValue({
    ok: true,
    json: async () => MIXED_SCORE_RESPONSE,
  });

  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));

  // All three results visible by default.
  expect(await screen.findByText('Strong Match Role')).toBeInTheDocument();
  expect(screen.getByText('Partial Match Role')).toBeInTheDocument();
  expect(screen.getByText('Weak Match Role')).toBeInTheDocument();
  expect(screen.getByText(/3 matches/i)).toBeInTheDocument();

  // Filter to Good match (60%+): 0.92 stays, 0.5 and 0.2 drop out.
  fireEvent.change(screen.getByLabelText(/Minimum match score/i), {
    target: { value: 'good' },
  });

  expect(screen.getByText('Strong Match Role')).toBeInTheDocument();
  expect(screen.queryByText('Partial Match Role')).not.toBeInTheDocument();
  expect(screen.queryByText('Weak Match Role')).not.toBeInTheDocument();
  expect(screen.getByText(/1 of 3 matches/i)).toBeInTheDocument();
});
