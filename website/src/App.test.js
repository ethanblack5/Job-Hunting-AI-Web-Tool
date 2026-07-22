import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders the search form on load', () => {
  render(<App />);
  expect(screen.getByText(/Job Hunting AI Web Tool/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Job Title/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Search Jobs/i })).toBeInTheDocument();
});

test('shows results page after search', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: /Search Jobs/i }));
  expect(screen.getByText(/5 matches/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /New Search/i })).toBeInTheDocument();
});
