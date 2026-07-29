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
