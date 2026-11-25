
function CompanyIntelligence({ intelligence }) {
  if (!intelligence?.available) {
    return (
      <section className="section">
        <h2>Company Data Availability</h2>
        <div className="intelligence-unavailable">
          Company intelligence is not available for this filing.
        </div>
      </section>
    );
  }

  const summary = intelligence.summary || {};
  const categories = intelligence.categories || [];

  function getStatusClass(status) {
    return status === "available"
      ? "status-available"
      : "status-not-found";
  }

  function getStatusLabel(status) {
    return status === "available"
      ? "Available"
      : "Not Found";
  }

  function renderEvidence(item) {
    const evidence = item.evidence || [];

    if (evidence.length === 0) {
      return (
        <p className="no-evidence">
          No supporting evidence excerpts were returned.
        </p>
      );
    }

    return (
      <div className="evidence-list">
        {evidence.map((entry, index) => (
          <div className="evidence-card" key={index}>
            <p className="evidence-source">
              Source: {entry.source_section || "SEC Filing"}
            </p>

            {entry.excerpt && (
              <p className="evidence-excerpt">
                {entry.excerpt}
              </p>
            )}

            {entry.details && (
              <div className="data-item-meta">
                {Object.entries(entry.details).map(([key, value]) => (
                  <span key={key}>
                    <strong>{key.replaceAll("_", " ")}:</strong>{" "}
                    {String(value)}
                  </span>
                ))}
              </div>
            )}

            {entry.matched_terms?.length > 0 && (
              <div className="matched-terms">
                {entry.matched_terms.map((term, termIndex) => (
                  <span className="matched-term" key={termIndex}>
                    {term}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="section">
      <h2>Company Data Availability</h2>

      <p className="intelligence-description">
        Inventory of company information identified across the retrieved
        SEC filings and Company Facts data. Expand a department to explore
        the available data points and their supporting evidence.
      </p>

      <div className="intelligence-summary">
        <div className="intelligence-stat">
          <span>Data Items Checked</span>
          <strong>
            {summary.total_data_items_checked ?? 0}
          </strong>
        </div>

        <div className="intelligence-stat">
          <span>Available Data Items</span>
          <strong>
            {summary.available_data_items ?? 0}
          </strong>
        </div>

        <div className="intelligence-stat">
          <span>Not Found</span>
          <strong>
            {summary.not_found_data_items ?? 0}
          </strong>
        </div>
      </div>

      <div className="department-list">
        {categories.map((category, categoryIndex) => {
          const items = category.data_items || [];

          const availableCount = items.filter(
            (item) => item.status === "available"
          ).length;

          const notFoundCount = items.length - availableCount;

          return (
            <details
              className="department-card"
              key={category.department || categoryIndex}
            >
              <summary className="department-header">
                <div>
                  <h3>{category.department}</h3>

                  <p>
                    {items.length} data items examined
                  </p>
                </div>

                <div className="department-counts">
                  <span className="count-available">
                    {availableCount} Available
                  </span>

                  <span className="count-not-found">
                    {notFoundCount} Not Found
                  </span>
                </div>
              </summary>

              <div className="department-content">
                {items.map((item, itemIndex) => (
                  <div className="data-item" key={item.name || itemIndex}>
                    <div className="data-item-header">
                      <h4>{item.name}</h4>

                      <span
                        className={`status-label ${getStatusClass(
                          item.status
                        )}`}
                      >
                        {getStatusLabel(item.status)}
                      </span>
                    </div>

                    <div className="data-item-meta">
                      <span>
                        Evidence blocks: {item.evidence_count ?? 0}
                      </span>

                      {item.source && (
                        <span>
                          Source:{" "}
                          {Array.isArray(item.source)
                            ? item.source.join(", ")
                            : item.source}
                        </span>
                      )}
                    </div>

                    {item.matched_terms?.length > 0 && (
                      <div className="matched-terms">
                        {item.matched_terms.map((term, termIndex) => (
                          <span className="matched-term" key={termIndex}>
                            {term}
                          </span>
                        ))}
                      </div>
                    )}

                    {item.evidence?.length > 0 && (
                      <details className="evidence-details">
                        <summary>
                          View supporting evidence ({item.evidence.length})
                        </summary>

                        {renderEvidence(item)}
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </details>
          );
        })}
      </div>

      {intelligence.limitations?.length > 0 && (
        <div className="intelligence-limitations">
          <h3>Data Coverage Limitations</h3>

          <ul>
            {intelligence.limitations.map((limitation, index) => (
              <li key={index}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}

      {intelligence.filing && (
        <p className="data-disclaimer">
          Inventory based on Form {intelligence.filing.form || "10-K"},
          filed on {intelligence.filing.filing_date || "an unspecified date"}.
          {" "}
          {intelligence.filing.url && (
            <a
              href={intelligence.filing.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              View original SEC filing ↗
            </a>
          )}
        </p>
      )}
    </section>
  );
}

export default CompanyIntelligence;
