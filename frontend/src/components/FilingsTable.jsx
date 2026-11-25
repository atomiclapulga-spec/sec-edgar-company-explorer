
import { useMemo, useState } from "react";

const FILING_FILTERS = [
  { id: "all", label: "All Filings" },
  { id: "annual", label: "Annual Reports" },
  { id: "quarterly", label: "Quarterly Reports" },
  { id: "current", label: "Current Reports" },
  { id: "proxy", label: "Proxy & Shareholder" },
  { id: "insider", label: "Insider Transactions" },
  { id: "other", label: "Other Filings" },
];

function getFilingCategory(form) {
  const normalized = (form || "").toUpperCase().trim();

  if (["10-K", "20-F", "40-F"].includes(normalized)) {
    return "annual";
  }

  if (normalized === "10-Q") {
    return "quarterly";
  }

  if (normalized === "8-K") {
    return "current";
  }

  if (
    ["DEF 14A", "DEFA14A", "PRE 14A", "PREC14A",
      "DEFC14A", "DEF 14C", "DEFM14A"].includes(normalized) ||
    normalized.includes("14A") ||
    normalized.includes("14C")
  ) {
    return "proxy";
  }

  if (["3", "4", "5", "3/A", "4/A", "5/A"].includes(normalized)) {
    return "insider";
  }

  return "other";
}

function FilingsTable({ filings = [] }) {
  const [activeFilter, setActiveFilter] = useState("all");

  const categorizedFilings = useMemo(
    () =>
      filings.map((filing) => ({
        ...filing,
        category: getFilingCategory(filing.form),
      })),
    [filings]
  );

  const counts = useMemo(() => {
    const result = { all: categorizedFilings.length };

    FILING_FILTERS.slice(1).forEach((filter) => {
      result[filter.id] = categorizedFilings.filter(
        (filing) => filing.category === filter.id
      ).length;
    });

    return result;
  }, [categorizedFilings]);

  const filteredFilings =
    activeFilter === "all"
      ? categorizedFilings
      : categorizedFilings.filter(
          (filing) => filing.category === activeFilter
        );

  if (!filings.length) {
    return (
      <section className="section">
        <h2>Recent SEC Filings</h2>
        <p className="no-filings">
          No recent filings are available for this company.
        </p>
      </section>
    );
  }

  return (
    <section className="section filings-section">
      <div className="section-heading">
        <div>
          <h2>Recent SEC Filings</h2>
          <p className="section-description">
            Browse regulatory submissions by filing category.
          </p>
        </div>
        <span className="filing-total">
          {filteredFilings.length} of {filings.length} filings
        </span>
      </div>

      <div className="filing-filters">
        {FILING_FILTERS.map((filter) => (
          <button
            key={filter.id}
            type="button"
            className={`filing-filter ${
              activeFilter === filter.id ? "active" : ""
            }`}
            onClick={() => setActiveFilter(filter.id)}
          >
            {filter.label}
            <span>{counts[filter.id]}</span>
          </button>
        ))}
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Form Type</th>
              <th>Filing Date</th>
              <th>Report Date</th>
              <th>Document</th>
            </tr>
          </thead>

          <tbody>
            {filteredFilings.map((filing, index) => (
              <tr
                key={`${filing.accession_number || filing.filing_date}-${filing.form}-${index}`}
              >
                <td>
                  <span className="filing-form">{filing.form}</span>
                </td>
                <td>{filing.filing_date || "N/A"}</td>
                <td>{filing.report_date || "N/A"}</td>
                <td>
                  {filing.url ? (
                    <a
                      href={filing.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      View Filing ↗
                    </a>
                  ) : (
                    <span className="unavailable-document">N/A</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredFilings.length === 0 && (
          <p className="no-filings">
            No filings found in this category.
          </p>
        )}
      </div>
    </section>
  );
}

export default FilingsTable;
