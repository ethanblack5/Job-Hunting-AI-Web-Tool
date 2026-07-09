import { useState } from 'react';

function SearchForm({ setResults }) {
  const [formData, setFormData] = useState({
    jobTitle: '',
    skills: '',
    location: '',
    experienceLevel: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
  e.preventDefault();

  const mockResults = [
    {
      id: 1,
      title: 'Senior Python Developer',
      company: 'Acme Corp',
      location: 'Remote',
      salary: '$120,000 - $150,000',
      type: 'Full-time',
      date: '2 days ago',
      description: 'We are looking for an experienced Python developer...',
      skills: ['Python', 'FastAPI', 'PostgreSQL'],
      link: 'https://remoteok.com',
      score: 0.92
    },
    {
      id: 2,
      title: 'Machine Learning Engineer',
      company: 'Tech Startup',
      location: 'Remote',
      salary: '$130,000 - $160,000',
      type: 'Full-time',
      date: '1 day ago',
      description: 'Join our ML team to build cutting edge models...',
      skills: ['Python', 'TensorFlow', 'AWS'],
      link: 'https://remoteok.com',
      score: 0.87
    },
    {
      id: 3,
      title: 'Backend API Developer',
      company: 'Remote First Inc',
      location: 'Remote',
      salary: '$100,000 - $130,000',
      type: 'Contract',
      date: '3 days ago',
      description: 'Build and maintain RESTful APIs for our platform...',
      skills: ['Python', 'Django', 'Docker'],
      link: 'https://remoteok.com',
      score: 0.81
    }
  ];

  setResults(mockResults);
};

  return (
    <form onSubmit={handleSubmit}>
      <h2>Find Your Next Remote Job</h2>

      <label>Job Title</label>
      <input
        type="text"
        name="jobTitle"
        value={formData.jobTitle}
        onChange={handleChange}
        placeholder="e.g. Software Engineer"
      />

      <label>Skills</label>
      <input
        type="text"
        name="skills"
        value={formData.skills}
        onChange={handleChange}
        placeholder="e.g. Python, React, Machine Learning"
      />

      <label>Location Preference</label>
      <input
        type="text"
        name="location"
        value={formData.location}
        onChange={handleChange}
        placeholder="e.g. United States"
      />

      <label>Experience Level</label>
      <select
        name="experienceLevel"
        value={formData.experienceLevel}
        onChange={handleChange}
      >
        <option value="">Select...</option>
        <option value="entry">Entry Level</option>
        <option value="mid">Mid Level</option>
        <option value="senior">Senior Level</option>
      </select>

      <button type="submit">Search Jobs</button>
    </form>
  );
}

export default SearchForm;