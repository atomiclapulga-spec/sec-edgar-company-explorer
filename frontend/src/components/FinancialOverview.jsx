
function formatCurrency(value, unit = "USD") {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return String(value);
  }

  if (unit !== "USD") {
    return `${numericValue.toLocaleString("en-US")} ${unit || ""}`;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(numericValue);
}

function HistoryTable({ records }) {
  if (!records || records.length === 0) {
    return null;
  }

  return (
    <div className="financial-history-table">
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Reporting Period</th>
              <th>Value</th>
              <th>Filing Date</th>
              <th>Form</th>
            </tr>
          </thead>

          <tbody>
            {records.map((record, index) => (
              <tr
                key={`${record.start || "point"}-${record.end}-${index}`}
              >
                <td>
                  {record.start
                    ? `${record.start} – ${record.end}`
                    : `As of ${record.end || "N/A"}`}
                </td>

                <td>
                  <strong>
                    {formatCurrency(record.value, record.unit)}
                  </strong>
                </td>

                <td>{record.filed || "N/A"}</td>

                <td>{record.form || "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FinancialHistory({ metric }) {
  const historyGroups = [
    {
      key: "quarterly_history",
      title: "Quarterly History",
    },
    {
      key: "annual_history",
      title: "Annual History",
    },
    {
      key: "year_to_date_history",
      title: "Year-to-Date History",
    },
    {
      key: "point_in_time_history",
      title: "Historical Balances",
    },
    {
      key: "unclassified_history",
      title: "Other Reported Periods",
    },
  ];

  const availableGroups = historyGroups
    .map((group) => ({
      ...group,
      records: metric[group.key] || [],
    }))
    .filter((group) => group.records.length > 0);

  if (availableGroups.length === 0) {
    return (
      <p className="no-history">
        No historical records are available for this metric.
      </p>
    );
  }

  return (
    <div className="financial-history-content">
      {availableGroups.map((group) => (
        <div className="financial-history-group" key={group.key}>
          <h4>
            {group.title}
            <span>{group.records.length} records</span>
          </h4>

          <HistoryTable records={group.records} />
        </div>
      ))}
    </div>
  );
}

function FinancialOverview({ financials }) {
  const metrics = Object.entries(financials || {});

  if (metrics.length === 0) {
    return (
      <section className="section">
        <h2>Financial Overview</h2>
        <p>No financial information available.</p>
      </section>
    );
  }

  return (
    <section className="section">
      <h2>Financial Overview</h2>

      <p className="financial-description">
        Latest reported financial figures from SEC Company Facts.
        Expand a metric to explore its historical reporting periods.
      </p>

      <div className="financial-grid">
        {metrics.map(([name, metric]) => {
          const value =
            metric.latest_value ??
            metric.value ??
            (typeof metric.latest === "number" ? metric.latest : null);

          const historyCount = [
            "quarterly_history",
            "annual_history",
            "year_to_date_history",
            "point_in_time_history",
            "unclassified_history",
          ].reduce(
            (total, key) => total + (metric[key]?.length || 0),
            0
          );

          return (
            <div className="financial-card" key={name}>
              <span>{name}</span>

              <strong>
                {formatCurrency(value, metric.unit)}
              </strong>

              <small>
                Period: {metric.period_start || "N/A"}
                {" – "}
                {metric.period_end || "Not specified"}
              </small>

              <small>
                Filing: {metric.form || "N/A"} ·{" "}
                {metric.filing_date || "Date unavailable"}
              </small>

              <small>
                Reporting type: {metric.period_type || "Not specified"}
              </small>

              {historyCount > 0 ? (
                <details className="financial-history">
                  <summary>
                    View financial history ({historyCount} records)
                  </summary>

                  <FinancialHistory metric={metric} />
                </details>
              ) : (
                <p className="no-history">
                  Historical data not available.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default FinancialOverview;
