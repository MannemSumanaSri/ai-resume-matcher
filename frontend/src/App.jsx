import { useState } from "react";
import axios from "axios";
import JobRanking from "./components/JobRanking";
import "./App.css";

function App() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [jobRanking, setJobRanking] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [error, setError] = useState("");
  const [rankingError, setRankingError] = useState("");

  const API_URL = (
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  const normalizeMatchResponse = (data) => {
    if (!data || typeof data !== "object") {
      return null;
    }

    if (
      data.semantic_score !== undefined ||
      data.tfidf_score !== undefined ||
      data.skill_match_score !== undefined ||
      data.final_match_score !== undefined
    ) {
      return data;
    }

    if (
      data.result &&
      typeof data.result === "object"
    ) {
      return normalizeMatchResponse(data.result);
    }

    if (
      data.data &&
      typeof data.data === "object"
    ) {
      return normalizeMatchResponse(data.data);
    }

    if (
      data.results &&
      typeof data.results === "object" &&
      !Array.isArray(data.results)
    ) {
      return normalizeMatchResponse(data.results);
    }

    return data;
  };

  const normalizeNumber = (value) => {
    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }

    if (typeof value === "string") {
      const trimmed = value.trim();

      if (!trimmed) {
        return null;
      }

      const parsed = Number(trimmed);

      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }

    return null;
  };

  const getScoreValue = (value) => {
    const normalized = normalizeNumber(value);

    return normalized === null ? "—" : normalized;
  };

  const handleAnalyze = async () => {
    if (!resume) {
      setError("Please upload your resume PDF.");
      return;
    }

    if (!jobDescription.trim()) {
      setError("Please enter a job description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();

      formData.append("resume", resume);
      formData.append(
        "job_description",
        jobDescription.trim()
      );

      const response = await axios.post(
        `${API_URL}/match`,
        formData,
        {
          timeout: 120000
        }
      );

      const backendData = response.data;

      console.log("BACKEND /match RESPONSE:", backendData);
      console.log(
        "BACKEND semantic_score:",
        backendData?.semantic_score
      );

      if (
        backendData?.error
      ) {
        throw new Error(
          backendData.error
        );
      }

      const normalizedResult =
        normalizeMatchResponse(
          backendData
        );

      if (!normalizedResult) {
        throw new Error(
          "Invalid response received from backend."
        );
      }

      setResult(normalizedResult);
    } catch (err) {
      console.error(
        "RESUME ANALYSIS ERROR:",
        err
      );

      if (
        err.code === "ECONNABORTED"
      ) {
        setError(
          "Analysis is taking longer than expected. Please try again."
        );
      } else if (
        err.response
      ) {
        setError(
          `Server error: ${
            err.response.data?.detail ||
            err.response.data?.error ||
            err.response.status
          }`
        );
      } else if (
        err.message
      ) {
        setError(
          err.message
        );
      } else {
        setError(
          "Unable to connect to the backend. Make sure FastAPI is running."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const findBestJobs = async () => {
    if (!resume) {
      setRankingError(
        "Please upload your resume PDF first."
      );
      return;
    }

    setRankingLoading(true);
    setRankingError("");
    setJobRanking([]);

    const jobs = [
      {
        title: "Frontend Developer",
        description:
          "We are looking for a frontend developer with JavaScript, React, HTML, CSS, Git and REST API experience."
      },
      {
        title: "Python Backend Developer",
        description:
          "We are looking for a Python backend developer with Python, Node.js, Express, MongoDB, PostgreSQL, SQL, REST API and Git experience."
      },
      {
        title: "Full Stack Developer",
        description:
          "We are looking for a full stack developer with JavaScript, React, Node.js, Express, MongoDB, SQL, Git and Docker experience."
      },
      {
        title: "Cloud Developer",
        description:
          "We are looking for a cloud developer with Python, AWS, Docker, Kubernetes and cloud deployment experience."
      },
      {
        title: "Software Developer",
        description:
          "We are looking for a software developer with Python, JavaScript, React, Node.js, Express, MongoDB, SQL, Git, Docker and AWS."
      }
    ];

    const formData = new FormData();

    formData.append(
      "resume",
      resume
    );

    formData.append(
      "jobs",
      JSON.stringify(jobs)
    );

    try {
      const response = await axios.post(
        `${API_URL}/match-multiple-pdf`,
        formData,
        {
          timeout: 120000
        }
      );

      console.log(
        "BACKEND /match-multiple-pdf RESPONSE:",
        response.data
      );

      if (
        response.data?.error
      ) {
        setRankingError(
          response.data.error
        );
        return;
      }

      const backendResults =
        Array.isArray(response.data?.results)
          ? response.data.results
          : [];

      setJobRanking(
        backendResults
      );
    } catch (err) {
      console.error(
        "JOB RANKING ERROR:",
        err
      );

      if (
        err.response
      ) {
        setRankingError(
          `Server error: ${
            err.response.data?.detail ||
            err.response.data?.error ||
            err.response.status
          }`
        );
      } else if (
        err.code === "ECONNABORTED"
      ) {
        setRankingError(
          "Job matching is taking longer than expected. Please try again."
        );
      } else {
        setRankingError(
          "Unable to connect to the backend. Make sure FastAPI is running."
        );
      }
    } finally {
      setRankingLoading(false);
    }
  };

  const getScoreClass = (score) => {
    const value = normalizeNumber(score);

    if (value === null) {
      return "score-low";
    }

    if (value >= 75) {
      return "score-excellent";
    }

    if (value >= 50) {
      return "score-good";
    }

    if (value >= 30) {
      return "score-average";
    }

    return "score-low";
  };

  const getScoreMessage = (score) => {
    const value = normalizeNumber(score);

    if (value === null) {
      return "Match score is unavailable.";
    }

    if (value >= 80) {
      return "Excellent match! Your resume is highly aligned with this job.";
    }

    if (value >= 65) {
      return "Strong match! You have most of the skills required.";
    }

    if (value >= 50) {
      return "Good match, but there are some skills you should improve.";
    }

    if (value >= 30) {
      return "Moderate match. Consider improving your resume for this role.";
    }

    return "Low match. You should work on the missing skills.";
  };

  const handleFileChange = (event) => {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    if (
      selectedFile.type !==
      "application/pdf"
    ) {
      setError(
        "Please upload a PDF file."
      );

      setResume(null);
      return;
    }

    setResume(
      selectedFile
    );

    setError("");
    setResult(null);
    setJobRanking([]);
    setRankingError("");
  };

  const handleClear = () => {
    setResume(null);
    setJobDescription("");
    setResult(null);
    setJobRanking([]);
    setError("");
    setRankingError("");

    const fileInput =
      document.getElementById(
        "resume-upload"
      );

    if (fileInput) {
      fileInput.value = "";
    }
  };

  const semanticScore =
    getScoreValue(
      result?.semantic_score
    );

  const tfidfScore =
    getScoreValue(
      result?.tfidf_score
    );

  const skillMatchScore =
    getScoreValue(
      result?.skill_match_score
    );

  const finalMatchScore =
    getScoreValue(
      result?.final_match_score
    );

  return (
    <div className="app">
      <header className="header">
        <div className="header-icon">
          🤖
        </div>

        <h1>
          AI Resume & Job Matcher
        </h1>

        <p>
          Analyze your resume against a job description using
          AI-powered semantic matching, skill analysis and
          resume intelligence.
        </p>
      </header>

      <main className="container">
        <div className="input-section">
          <div className="input-card">
            <div className="card-icon">
              📄
            </div>

            <h2>
              Upload Resume
            </h2>

            <p className="input-description">
              Upload your resume in PDF format.
            </p>

            <label
              htmlFor="resume-upload"
              className="upload-box"
            >
              <span className="upload-icon">
                📤
              </span>

              <span>
                Click to upload your resume
              </span>

              <small>
                PDF files only
              </small>
            </label>

            <input
              id="resume-upload"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="file-input"
            />

            {resume && (
              <div className="file-name">
                <span>
                  ✓
                </span>

                {resume.name}
              </div>
            )}
          </div>

          <div className="input-card">
            <div className="card-icon">
              💼
            </div>

            <h2>
              Job Description
            </h2>

            <p className="input-description">
              Paste the job description you want to compare
              your resume against.
            </p>

            <textarea
              rows="10"
              placeholder="Paste the job description here..."
              value={jobDescription}
              onChange={(event) =>
                setJobDescription(
                  event.target.value
                )
              }
            />

            <div className="character-count">
              {jobDescription.length} characters
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            ⚠️
            <span>
              {error}
            </span>
          </div>
        )}

        <div className="analyze-container">
          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                Analyzing Resume...
              </>
            ) : (
              <>
                ✨ Analyze Resume
              </>
            )}
          </button>

          <button
            className="analyze-button"
            onClick={findBestJobs}
            disabled={rankingLoading}
          >
            {rankingLoading ? (
              <>
                <span className="loading-spinner"></span>
                Finding Jobs...
              </>
            ) : (
              <>
                🔎 Find Best Job Matches
              </>
            )}
          </button>

          {(result ||
            jobRanking.length > 0) && (
            <button
              className="clear-button"
              onClick={handleClear}
            >
              Clear
            </button>
          )}
        </div>

        {rankingError && (
          <div className="error-message">
            ⚠️
            <span>
              {rankingError}
            </span>
          </div>
        )}

        {jobRanking.length > 0 && (
          <JobRanking
            results={jobRanking}
          />
        )}

        {result && (
          <section className="results">
            <div className="score-section">
              <div className="section-title">
                <div>
                  <h2>
                    🎯 Resume Match Result
                  </h2>

                  <p>
                    How closely your resume matches this
                    job description.
                  </p>
                </div>
              </div>

              <div
                className={`main-score ${getScoreClass(
                  finalMatchScore
                )}`}
              >
                <span>
                  {finalMatchScore === "—"
                    ? "—"
                    : `${finalMatchScore}%`}
                </span>

                <small>
                  Overall Match
                </small>
              </div>

              <p className="score-description">
                {getScoreMessage(
                  finalMatchScore
                )}
              </p>

              <div className="score-grid">
                <div className="score-card">
                  <div className="score-card-icon">
                    🔤
                  </div>

                  <h3>
                    TF-IDF
                  </h3>

                  <p>
                    {tfidfScore === "—"
                      ? "—"
                      : `${tfidfScore}%`}
                  </p>

                  <span>
                    Keyword similarity
                  </span>
                </div>

                <div className="score-card">
                  <div className="score-card-icon">
                    🧠
                  </div>

                  <h3>
                    Semantic
                  </h3>

                  <p>
                    {semanticScore === "—"
                      ? "—"
                      : `${semanticScore}%`}
                  </p>

                  <span>
                    Meaning similarity
                  </span>
                </div>

                <div className="score-card">
                  <div className="score-card-icon">
                    🛠️
                  </div>

                  <h3>
                    Skills
                  </h3>

                  <p>
                    {skillMatchScore === "—"
                      ? "—"
                      : `${skillMatchScore}%`}
                  </p>

                  <span>
                    Required skills matched
                  </span>
                </div>
              </div>
            </div>

            <div className="skills-section">
              <h2>
                📋 Resume Skills
              </h2>

              <p className="section-description">
                Technical skills detected from your resume.
              </p>

              <div className="skills-list">
                {result.resume_skills?.length > 0 ? (
                  result.resume_skills.map(
                    (skill, index) => (
                      <span
                        className="skill"
                        key={`${skill}-${index}`}
                      >
                        {skill}
                      </span>
                    )
                  )
                ) : (
                  <p>
                    No skills detected.
                  </p>
                )}
              </div>
            </div>

            <div className="skills-section matched-section">
              <h2>
                ✅ Matched Skills
              </h2>

              <p className="section-description">
                Skills found in both your resume and the
                job description.
              </p>

              <div className="skills-list">
                {result.matched_skills?.length > 0 ? (
                  result.matched_skills.map(
                    (skill, index) => (
                      <span
                        className="skill matched"
                        key={`${skill}-${index}`}
                      >
                        ✓ {skill}
                      </span>
                    )
                  )
                ) : (
                  <p>
                    No matching skills found.
                  </p>
                )}
              </div>
            </div>

            <div className="skills-section missing-section">
              <h2>
                ⚠️ Missing Skills
              </h2>

              <p className="section-description">
                Skills required by the job that were not
                detected in your resume.
              </p>

              <div className="skills-list">
                {result.missing_skills?.length > 0 ? (
                  result.missing_skills.map(
                    (skill, index) => (
                      <span
                        className="skill missing"
                        key={`${skill}-${index}`}
                      >
                        ⚠ {skill}
                      </span>
                    )
                  )
                ) : (
                  <div className="success-message">
                    🎉 No major missing skills detected!
                  </div>
                )}
              </div>
            </div>

            <div className="recommendations-section">
              <div className="recommendations-header">
                <div>
                  <h2>
                    🤖 AI Skill Recommendations
                  </h2>

                  <p>
                    Personalized learning suggestions based
                    on the skills missing from this job match.
                  </p>
                </div>

                <div className="ai-badge">
                  AI POWERED
                </div>
              </div>

              {result.recommendations?.length > 0 ? (
                <div className="recommendations-grid">
                  {result.recommendations.map(
                    (recommendation, index) => (
                      <div
                        className="recommendation-card"
                        key={`${recommendation.skill}-${index}`}
                      >
                        <div className="recommendation-title">
                          <span className="recommendation-icon">
                            🎯
                          </span>

                          <h3>
                            {recommendation.skill}
                          </h3>
                        </div>

                        <p className="recommendation-reason">
                          {recommendation.reason}
                        </p>

                        <h4>
                          Recommended Topics
                        </h4>

                        <div className="topics-list">
                          {recommendation.topics?.map(
                            (topic, topicIndex) => (
                              <span
                                className="topic"
                                key={`${topic}-${topicIndex}`}
                              >
                                {topic}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              ) : (
                <div className="no-recommendations">
                  🎉 Your resume already covers the
                  major skills required for this job!
                </div>
              )}
            </div>

            {result.resume_analysis && (
              <div className="resume-analysis-section">
                <div className="analysis-header">
                  <div>
                    <h2>
                      📊 Resume Strength Analysis
                    </h2>

                    <p>
                      Analysis of your resume structure,
                      content and technical skills.
                    </p>
                  </div>

                  <div className="strength-score">
                    <span>
                      {getScoreValue(
                        result.resume_analysis
                          .strength_score
                      )}
                      %
                    </span>

                    <small>
                      Resume Strength
                    </small>
                  </div>
                </div>

                <div className="analysis-stats">
                  <div className="analysis-stat">
                    <span>
                      📝
                    </span>

                    <strong>
                      {result.resume_analysis.word_count ?? "—"}
                    </strong>

                    <p>
                      Words
                    </p>
                  </div>

                  <div className="analysis-stat">
                    <span>
                      💻
                    </span>

                    <strong>
                      {result.resume_analysis.skill_count ?? "—"}
                    </strong>

                    <p>
                      Skills
                    </p>
                  </div>

                  <div className="analysis-stat">
                    <span>
                      📂
                    </span>

                    <strong>
                      {result.resume_analysis
                        .detected_sections
                        ?.length ?? 0}
                    </strong>

                    <p>
                      Sections
                    </p>
                  </div>
                </div>

                <div className="analysis-block">
                  <h3>
                    📂 Detected Resume Sections
                  </h3>

                  <div className="section-tags">
                    {result.resume_analysis
                      .detected_sections?.length > 0 ? (
                      result.resume_analysis
                        .detected_sections
                        .map(
                          (section, index) => (
                            <span
                              className="section-tag"
                              key={`${section}-${index}`}
                            >
                              ✓ {section}
                            </span>
                          )
                        )
                    ) : (
                      <p>
                        No standard sections detected.
                      </p>
                    )}
                  </div>
                </div>

                <div className="analysis-block">
                  <h3>
                    💪 Strengths
                  </h3>

                  {result.resume_analysis
                    .strengths?.length > 0 ? (
                    <div className="feedback-list">
                      {result.resume_analysis
                        .strengths
                        .map(
                          (strength, index) => (
                            <div
                              className="feedback-item strength-item"
                              key={`${strength}-${index}`}
                            >
                              <span>
                                ✓
                              </span>

                              <p>
                                {strength}
                              </p>
                            </div>
                          )
                        )}
                    </div>
                  ) : (
                    <p>
                      No specific strengths detected.
                    </p>
                  )}
                </div>

                <div className="analysis-block">
                  <h3>
                    💡 Improvement Suggestions
                  </h3>

                  {result.resume_analysis
                    .suggestions?.length > 0 ? (
                    <div className="feedback-list">
                      {result.resume_analysis
                        .suggestions
                        .map(
                          (suggestion, index) => (
                            <div
                              className="feedback-item suggestion-item"
                              key={`${suggestion}-${index}`}
                            >
                              <span>
                                !
                              </span>

                              <p>
                                {suggestion}
                              </p>
                            </div>
                          )
                        )}
                    </div>
                  ) : (
                    <div className="success-message">
                      🎉 No major improvements detected.
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        )}
      </main>

      <footer className="footer">
        <strong>
          AI Resume & Job Matcher
        </strong>

        <br />

        <span>
          Powered by TF-IDF + Semantic Similarity +
          Skill Analysis + AI Recommendations
        </span>
      </footer>
    </div>
  );
}

export default App;