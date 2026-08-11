import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // =========================================================
  // ANALYZE RESUME
  // =========================================================

  const handleAnalyze = async () => {
    // Validate resume
    if (!resume) {
      setError("Please upload your resume PDF.");
      return;
    }

    // Validate job description
    if (!jobDescription.trim()) {
      setError("Please enter a job description.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    // Create multipart form data
    const formData = new FormData();

    formData.append("resume", resume);
    formData.append("job_description", jobDescription);

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/match`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResult(response.data);
    } catch (err) {
      console.error(err);

      if (err.response) {
        setError(
          `Server error: ${
            err.response.data?.detail ||
            err.response.data?.error ||
            err.response.status
          }`
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


  // =========================================================
  // SCORE COLOR
  // =========================================================

  const getScoreClass = (score) => {
    if (score >= 75) {
      return "score-excellent";
    }

    if (score >= 50) {
      return "score-good";
    }

    if (score >= 30) {
      return "score-average";
    }

    return "score-low";
  };


  // =========================================================
  // SCORE MESSAGE
  // =========================================================

  const getScoreMessage = (score) => {
    if (score >= 80) {
      return "Excellent match! Your resume is highly aligned with this job.";
    }

    if (score >= 65) {
      return "Strong match! You have most of the skills required.";
    }

    if (score >= 50) {
      return "Good match, but there are some skills you should improve.";
    }

    if (score >= 30) {
      return "Moderate match. Consider improving your resume for this role.";
    }

    return "Low match. You should work on the missing skills.";
  };


  // =========================================================
  // FILE CHANGE
  // =========================================================

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (!selectedFile) {
      return;
    }

    if (selectedFile.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      setResume(null);
      return;
    }

    setResume(selectedFile);
    setError("");
  };


  // =========================================================
  // CLEAR RESULTS
  // =========================================================

  const handleClear = () => {
    setResume(null);
    setJobDescription("");
    setResult(null);
    setError("");

    const fileInput = document.getElementById("resume-upload");

    if (fileInput) {
      fileInput.value = "";
    }
  };


  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

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


      {/* =====================================================
          MAIN CONTAINER
      ===================================================== */}

      <main className="container">


        {/* ===================================================
            INPUT SECTION
        =================================================== */}

        <div className="input-section">


          {/* -------------------------------------------------
              RESUME UPLOAD
          ------------------------------------------------- */}

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


          {/* -------------------------------------------------
              JOB DESCRIPTION
          ------------------------------------------------- */}

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
                setJobDescription(event.target.value)
              }
            />

            <div className="character-count">
              {jobDescription.length} characters
            </div>

          </div>

        </div>


        {/* ===================================================
            ERROR
        =================================================== */}

        {error && (

          <div className="error-message">

            ⚠️

            <span>
              {error}
            </span>

          </div>

        )}


        {/* ===================================================
            BUTTONS
        =================================================== */}

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


          {result && (

            <button
              className="clear-button"
              onClick={handleClear}
            >
              Clear
            </button>

          )}

        </div>


        {/* ===================================================
            RESULTS
        =================================================== */}

        {result && (

          <section className="results">


            {/* =================================================
                OVERALL SCORE
            ================================================= */}

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
                  result.final_match_score
                )}`}
              >

                <span>
                  {result.final_match_score}%
                </span>

                <small>
                  Overall Match
                </small>

              </div>


              <p className="score-description">
                {getScoreMessage(
                  result.final_match_score
                )}
              </p>


              {/* SCORE BREAKDOWN */}

              <div className="score-grid">


                <div className="score-card">

                  <div className="score-card-icon">
                    🔤
                  </div>

                  <h3>
                    TF-IDF
                  </h3>

                  <p>
                    {result.tfidf_score}%
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
                    {result.semantic_score}%
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
                    {result.skill_match_score}%
                  </p>

                  <span>
                    Required skills matched
                  </span>

                </div>

              </div>

            </div>


            {/* =================================================
                RESUME SKILLS
            ================================================= */}

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
                        key={index}
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


            {/* =================================================
                MATCHED SKILLS
            ================================================= */}

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
                        key={index}
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


            {/* =================================================
                MISSING SKILLS
            ================================================= */}

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
                        key={index}
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


            {/* =================================================
                AI RECOMMENDATIONS
            ================================================= */}

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
                        key={index}
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
                                key={topicIndex}
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


            {/* =================================================
                RESUME STRENGTH ANALYSIS
            ================================================= */}

            {result.resume_analysis && (

              <div className="resume-analysis-section">


                {/* HEADER */}

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
                      {result.resume_analysis.strength_score}%
                    </span>

                    <small>
                      Resume Strength
                    </small>

                  </div>

                </div>


                {/* STATS */}

                <div className="analysis-stats">


                  <div className="analysis-stat">

                    <span>
                      📝
                    </span>

                    <strong>
                      {result.resume_analysis.word_count}
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
                      {result.resume_analysis.skill_count}
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
                      {result.resume_analysis.detected_sections?.length || 0}
                    </strong>

                    <p>
                      Sections
                    </p>

                  </div>

                </div>


                {/* DETECTED SECTIONS */}

                <div className="analysis-block">

                  <h3>
                    📂 Detected Resume Sections
                  </h3>


                  <div className="section-tags">

                    {result.resume_analysis.detected_sections?.length > 0 ? (

                      result.resume_analysis.detected_sections.map(
                        (section, index) => (

                          <span
                            className="section-tag"
                            key={index}
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


                {/* STRENGTHS */}

                <div className="analysis-block">

                  <h3>
                    💪 Strengths
                  </h3>


                  {result.resume_analysis.strengths?.length > 0 ? (

                    <div className="feedback-list">

                      {result.resume_analysis.strengths.map(
                        (strength, index) => (

                          <div
                            className="feedback-item strength-item"
                            key={index}
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


                {/* SUGGESTIONS */}

                <div className="analysis-block">

                  <h3>
                    💡 Improvement Suggestions
                  </h3>


                  {result.resume_analysis.suggestions?.length > 0 ? (

                    <div className="feedback-list">

                      {result.resume_analysis.suggestions.map(
                        (suggestion, index) => (

                          <div
                            className="feedback-item suggestion-item"
                            key={index}
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


      {/* =====================================================
          FOOTER
      ===================================================== */}

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