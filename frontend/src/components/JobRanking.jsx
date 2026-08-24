function JobRanking({ results }) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <section className="job-ranking">

      <div className="ranking-header">
        <div>
          <span className="ranking-label">🤖 AI JOB DISCOVERY</span>

          <h2>Best Job Matches</h2>

          <p>
            Jobs ranked according to how closely they match your resume.
          </p>
        </div>

        <div className="job-count">
          {results.length} Jobs
        </div>
      </div>

      <div className="ranking-list">

        {results.map((job) => {

          const score = Number(job.final_match_score || 0);

          let scoreClass = "low";

          if (score >= 80) {
            scoreClass = "excellent";
          } else if (score >= 60) {
            scoreClass = "good";
          } else if (score >= 40) {
            scoreClass = "average";
          }

          return (
            <div
              className={`job-ranking-card ${scoreClass}`}
              key={`${job.rank}-${job.title}`}
            >

              {/* Rank */}
              <div className="job-rank">
                #{job.rank}
              </div>

              {/* Job information */}
              <div className="job-info">

                <h3>{job.title}</h3>

                <div className="job-metrics">

                  <span>
                    🔤 TF-IDF: {Number(job.tfidf_score).toFixed(2)}%
                  </span>

                  <span>
                    🧠 Semantic:{" "}
                    {Number(job.semantic_score).toFixed(2)}%
                  </span>

                  <span>
                    🛠️ Skills:{" "}
                    {Number(job.skill_match_score).toFixed(2)}%
                  </span>

                </div>

                {job.matched_skills?.length > 0 && (
                  <div className="ranking-skills">

                    <strong>Matched:</strong>

                    {job.matched_skills.map((skill) => (
                      <span
                        className="ranking-skill matched"
                        key={skill}
                      >
                        ✓ {skill}
                      </span>
                    ))}

                  </div>
                )}

                {job.missing_skills?.length > 0 && (
                  <div className="ranking-skills">

                    <strong>Missing:</strong>

                    {job.missing_skills.map((skill) => (
                      <span
                        className="ranking-skill missing"
                        key={skill}
                      >
                        ⚠ {skill}
                      </span>
                    ))}

                  </div>
                )}

              </div>

              {/* Score */}
              <div className="job-score">

                <strong>
                  {score.toFixed(2)}%
                </strong>

                <span>Match</span>

              </div>

            </div>
          );
        })}

      </div>

    </section>
  );
}

export default JobRanking;