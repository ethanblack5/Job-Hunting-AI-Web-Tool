import { useState } from 'react';
import { MOCK_RESPONSE } from '../mock/mockResponse';

function SearchForm({ setSearchResponse }) {
  const [jobTitle, setJobTitle] = useState('');
  const [location, setLocation] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('');
  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState('');

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
    }
    setSkillInput('');
  };

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill();
    }
  };

  const removeSkill = (skill) => {
    setSkills(skills.filter((s) => s !== skill));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Request shape per docs/frontend-data-contract.md
    const request = {
      job_title: jobTitle,
      skills,
      location: location || 'remote',
      experience_level: experienceLevel,
      top_n: 20,
    };

    try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      throw new Error(
        errorData?.detail ||
          `Backend returned status ${response.status}`
      );
    }

    const responseData = await response.json()

    setSearchResponse(responseData);

  } catch (error) {
    console.error('Job search failed:', error);
  }
};

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <h2>Find Your Next Remote Job</h2>

      <label htmlFor="jobTitle">Job Title / Keywords</label>
      <input
        id="jobTitle"
        type="text"
        value={jobTitle}
        onChange={(e) => setJobTitle(e.target.value)}
        placeholder="e.g. Software Engineer"
      />

      <label htmlFor="skillInput">Skills</label>
      <div className="skill-input-row">
        <input
          id="skillInput"
          type="text"
          value={skillInput}
          onChange={(e) => setSkillInput(e.target.value)}
          onKeyDown={handleSkillKeyDown}
          placeholder="Type a skill, press Enter to add"
        />
        <button type="button" className="btn-secondary" onClick={addSkill}>
          Add
        </button>
      </div>
      {skills.length > 0 && (
        <div className="skill-tags" aria-label="Selected skills">
          {skills.map((skill) => (
            <span key={skill} className="skill-tag">
              {skill}
              <button
                type="button"
                className="skill-tag-remove"
                onClick={() => removeSkill(skill)}
                aria-label={`Remove ${skill}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <label htmlFor="location">Location Preference</label>
      <input
        id="location"
        type="text"
        value={location}
        onChange={(e) => setLocation(e.target.value)}
        placeholder="e.g. United States"
      />

      <label htmlFor="experienceLevel">Experience Level</label>
      <select
        id="experienceLevel"
        value={experienceLevel}
        onChange={(e) => setExperienceLevel(e.target.value)}
      >
        <option value="">No preference</option>
        <option value="internship">Internship</option>
        <option value="entry">Entry Level</option>
        <option value="mid">Mid Level</option>
        <option value="senior">Senior Level</option>
        <option value="lead">Lead</option>
        <option value="staff">Staff</option>
        <option value="principal">Principal</option>
      </select>

      <button type="submit" className="btn-primary">
        Search Jobs
      </button>
    </form>
  );
}

export default SearchForm;
