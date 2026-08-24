function ScoreCard({ icon, title, score, subtitle }) {
  return (
    <div className="score-card">
      <div className="score-icon">{icon}</div>
      <div>
        <p className="score-title">{title}</p>
        <h3>{Number(score).toFixed(2)}%</h3>
        <span>{subtitle}</span>
      </div>
    </div>
  );
}

function SkillChip({ children, type }) {
  return (
    <span className={`skill-chip ${type || ""}`}>
      {type === "matched" && "✓ "}
      {type === "missing" && "⚠ "}
      {children}
    </span>
  );
}

function MatchResult({ result }) {
  if (!result) return null;

  const {
    final_match_score = 0,
    tfidf_score = 0,
    semantic_score = 0,
    skill_match_score = 0,
    resume_skills = [],
    matched_skills = [],
    missing_skills = [],
    recommendations = [],
    resume_analysis = {},
  } = result;

  const getMatchMessage = (score) => {
    if (score >= 80) {
      return "Excellent match! Your resume strongly fits this job.";
    }

    if (score >= 65) {
      return "Good match! You have most of the required skills.";
    }

    if (score >= 50) {
      return "Good potential, but there are some skills you should improve.";
    }

    return "Your resume needs improvement to better match this job.";
  };

  const getScoreClass = (score) => {
    if (score >= 80) return "excellent";
    if (score >= 60) return "good";
    if (score >= 40) return "average";
    return "low";
  };

  return (
    <section className="match-result">

      {/* Header */}
      <div className="result-header">
        <div>
          <span className="result-label">🎯 AI ANALYSIS</span>
          <h2>Resume Match Result</h2>
          <p>
            How closely your resume matches this job description.
          </p>
        </div>
      </div>

      {/* Main Score */}
      <div className={`main-score-card ${getScoreClass(final_match_score)}`}>
        <div className="score-circle">
          <div>
            <strong>{Number(final_match_score).toFixed(2)}%</strong>
            <span>Match</span>
          </div>
        </div>

        <div className="main-score-info">
          <span className="score-badge">
            {getScoreClass(final_match_score).toUpperCase()}
          </span>

          <h3>{getMatchMessage(final_match_score)}</h3>

          <p>
            This score combines keyword similarity, semantic similarity,
            and required skill matching.
          </p>
        </div>
      </div>

      {/* Score Cards */}
      <div className="score-grid">

        <ScoreCard
          icon="🔤"
          title="TF-IDF"
          score={tfidf_score}
          subtitle="Keyword similarity"
        />

        <ScoreCard
          icon="🧠"
          title="Semantic"
          score={semantic_score}
          subtitle="Meaning similarity"
        />

        <ScoreCard
          icon="🛠️"
          title="Skills"
          score={skill_match_score}
          subtitle="Required skills matched"
        />

      </div>

      {/* Resume Skills */}
      <div className="result-section">
        <div className="section-heading">
          <div className="section-icon">📋</div>
          <div>
            <h3>Resume Skills</h3>
            <p>Technical skills detected from your resume.</p>
          </div>
        </div>

        <div className="skills-container">
          {resume_skills.length > 0 ? (
            resume_skills.map((skill, index) => (
              <SkillChip key={index}>{skill}</SkillChip>
            ))
          ) : (
            <p className="empty-text">No skills detected.</p>
          )}
        </div>
      </div>

      {/* Matched Skills */}
      <div className="result-section">
        <div className="section-heading">
          <div className="section-icon matched-icon">✓</div>
          <div>
            <h3>Matched Skills</h3>
            <p>Skills found in both your resume and the job description.</p>
          </div>
        </div>

        <div className="skills-container">
          {matched_skills.length > 0 ? (
            matched_skills.map((skill, index) => (
              <SkillChip key={index} type="matched">
                {skill}
              </SkillChip>
            ))
          ) : (
            <p className="empty-text">No matched skills found.</p>
          )}
        </div>
      </div>

      {/* Missing Skills */}
      <div className="result-section">
        <div className="section-heading">
          <div className="section-icon missing-icon">⚠</div>
          <div>
            <h3>Missing Skills</h3>
            <p>Skills required by the job that were not detected.</p>
          </div>
        </div>

        <div className="skills-container">
          {missing_skills.length > 0 ? (
            missing_skills.map((skill, index) => (
              <SkillChip key={index} type="missing">
                {skill}
              </SkillChip>
            ))
          ) : (
            <div className="success-message">
              🎉 No missing skills detected!
            </div>
          )}
        </div>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="result-section">
          <div className="section-heading">
            <div className="section-icon ai-icon">🤖</div>
            <div>
              <h3>AI Skill Recommendations</h3>
              <p>
                Personalized learning suggestions based on your skill gaps.
              </p>
            </div>
          </div>

          <div className="recommendation-grid">
            {recommendations.map((recommendation, index) => (
              <div className="recommendation-card" key={index}>

                <div className="recommendation-top">
                  <div className="recommendation-skill-icon">
                    🎯
                  </div>

                  <div>
                    <h4>{recommendation.skill}</h4>
                    <span className="ai-powered">AI POWERED</span>
                  </div>
                </div>

                <p className="recommendation-reason">
                  {recommendation.reason}
                </p>

                {recommendation.topics &&
                  recommendation.topics.length > 0 && (
                    <div>
                      <h5>Recommended Topics</h5>

                      <div className="topic-list">
                        {recommendation.topics.map((topic, topicIndex) => (
                          <span key={topicIndex}>
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resume Analysis */}
      {resume_analysis && (
        <div className="result-section">

          <div className="section-heading">
            <div className="section-icon analysis-icon">📊</div>
            <div>
              <h3>Resume Strength Analysis</h3>
              <p>
                Analysis of your resume structure, content and technical
                skills.
              </p>
            </div>
          </div>

          {/* Resume Strength */}
          <div className="resume-strength">

            <div className="strength-score">
              <strong>
                {Number(resume_analysis.strength_score || 0).toFixed(2)}%
              </strong>

              <span>Resume Strength</span>
            </div>

            <div className="strength-bar-container">
              <div className="strength-bar">
                <div
                  className="strength-fill"
                  style={{
                    width: `${Math.min(
                      Number(resume_analysis.strength_score || 0),
                      100
                    )}%`,
                  }}
                ></div>
              </div>
            </div>

          </div>

          {/* Statistics */}
          <div className="resume-stats">

            <div className="resume-stat">
              <span>📝</span>
              <strong>{resume_analysis.word_count || 0}</strong>
              <small>Words</small>
            </div>

            <div className="resume-stat">
              <span>💻</span>
              <strong>{resume_analysis.skill_count || 0}</strong>
              <small>Skills</small>
            </div>

            <div className="resume-stat">
              <span>📂</span>
              <strong>
                {resume_analysis.detected_sections?.length || 0}
              </strong>
              <small>Sections</small>
            </div>

          </div>

          {/* Detected Sections */}
          {resume_analysis.detected_sections?.length > 0 && (
            <div className="analysis-block">

              <h4>📂 Detected Resume Sections</h4>

              <div className="section-chip-list">
                {resume_analysis.detected_sections.map(
                  (section, index) => (
                    <span key={index}>
                      ✓ {section}
                    </span>
                  )
                )}
              </div>

            </div>
          )}

          {/* Strengths */}
          {resume_analysis.strengths?.length > 0 && (
            <div className="analysis-block">

              <h4>💪 Strengths</h4>

              <div className="strength-list">
                {resume_analysis.strengths.map(
                  (strength, index) => (
                    <div key={index}>
                      <span>✓</span>
                      <p>{strength}</p>
                    </div>
                  )
                )}
              </div>

            </div>
          )}

          {/* Suggestions */}
          {resume_analysis.suggestions?.length > 0 && (
            <div className="analysis-block suggestions-block">

              <h4>💡 Improvement Suggestions</h4>

              <div className="suggestion-list">
                {resume_analysis.suggestions.map(
                  (suggestion, index) => (
                    <div key={index}>
                      <span>💡</span>
                      <p>{suggestion}</p>
                    </div>
                  )
                )}
              </div>

            </div>
          )}

          {(!resume_analysis.suggestions ||
            resume_analysis.suggestions.length === 0) && (
            <div className="success-message">
              🎉 No major improvements detected!
            </div>
          )}

        </div>
      )}

      {/* Footer */}
      <div className="result-footer">
        <span>🤖</span>
        <div>
          <strong>AI Resume & Job Matcher</strong>
          <p>
            Powered by TF-IDF + Semantic Similarity + Skill Analysis
            + AI Recommendations
          </p>
        </div>
      </div>

    </section>
  );
}

export default MatchResult;