// Mock backend response matching docs/frontend-data-contract.md.
// Includes nulls on purpose so null-safe rendering is exercised before
// the live endpoint exists.
export const MOCK_RESPONSE = {
  query_echo: {
    job_title: 'python developer',
    skills: ['python', 'fastapi'],
    location: 'remote',
    experience_level: 'mid',
  },
  match_count: 5,
  index_last_updated: '2026-07-18T14:32:00Z',
  results: [
    {
      id: 'remoteok-1049283',
      score: 0.92,
      title: 'Senior Python Developer',
      company: 'Acme Corp',
      location: 'Remote (US)',
      salary: '$120,000 - $150,000',
      role_type: 'full-time',
      date_listed: '2026-07-16T00:00:00Z',
      description:
        'We are looking for an experienced Python developer to build and maintain backend services powering our data platform.',
      skills: ['Python', 'FastAPI', 'PostgreSQL'],
      apply_url: 'https://remoteok.com',
    },
    {
      id: 'remoteok-1049311',
      score: 0.87,
      title: 'Machine Learning Engineer',
      company: 'Tech Startup',
      location: 'Remote (Worldwide)',
      salary: '$130,000 - $160,000',
      role_type: null,
      date_listed: '2026-07-17T00:00:00Z',
      description:
        'Join our ML team to build, train, and ship models that drive product recommendations at scale.',
      skills: ['Python', 'TensorFlow', 'AWS'],
      apply_url: 'https://remoteok.com',
    },
    {
      id: 'remoteok-1049358',
      score: 0.81,
      title: 'Backend API Developer',
      company: 'Remote First Inc',
      location: null,
      salary: null,
      role_type: 'contract',
      date_listed: '2026-07-15T00:00:00Z',
      description:
        'Build and maintain RESTful APIs for our platform, working closely with frontend and infrastructure teams.',
      skills: ['Python', 'Django', 'Docker'],
      apply_url: 'https://remoteok.com',
    },
    {
      id: 'remoteok-1049402',
      score: 0.74,
      title: 'Full Stack Engineer',
      company: null,
      location: 'Remote (Europe)',
      salary: '$90,000 - $115,000',
      role_type: 'full-time',
      date_listed: null,
      description:
        'Work across a modern React and Python stack shipping features end to end for a fast-growing SaaS product.',
      skills: ['React', 'Python', 'PostgreSQL'],
      apply_url: 'https://remoteok.com',
    },
    {
      id: 'remoteok-1049477',
      score: 0.61,
      title: 'Data Engineer',
      company: 'Signal Analytics',
      location: 'Remote (US)',
      salary: '$110,000 - $140,000',
      role_type: 'full-time',
      date_listed: '2026-07-10T00:00:00Z',
      description:
        'Design and operate data pipelines feeding analytics and ML workloads across the company.',
      skills: ['Python', 'SQL', 'Airflow', 'AWS'],
      apply_url: 'https://remoteok.com',
    },
  ],
  analytics: {
    skill_frequency: [
      { skill: 'python', count: 5 },
      { skill: 'aws', count: 2 },
      { skill: 'postgresql', count: 2 },
      { skill: 'react', count: 1 },
      { skill: 'docker', count: 1 },
    ],
  },
};
