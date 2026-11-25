
function CompanyOverview({ company }) {
  return (
    <section className="section">
      <h2>Company Overview</h2>

      <div className="overview-grid">
        <div className="info-card">
          <span>Company Name</span>
          <strong>{company.company_name || "N/A"}</strong>
        </div>

        <div className="info-card">
          <span>CIK</span>
          <strong>{company.cik || "N/A"}</strong>
        </div>

        <div className="info-card">
          <span>Ticker</span>
          <strong>{company.tickers?.join(", ") || "N/A"}</strong>
        </div>

        <div className="info-card">
          <span>Exchange</span>
          <strong>{company.exchanges?.join(", ") || "N/A"}</strong>
        </div>

        <div className="info-card">
          <span>SIC</span>
          <strong>{company.sic || "N/A"}</strong>
        </div>

        <div className="info-card">
          <span>Industry</span>
          <strong>{company.sic_description || "N/A"}</strong>
        </div>
      </div>

      <div className="address-card">
        <h3>Business Address</h3>

        <p>
          {[
            company.business_address?.street1,
            company.business_address?.street2,
            company.business_address?.city,
            company.business_address?.stateOrCountry,
            company.business_address?.zipCode,
          ]
            .filter(Boolean)
            .join(", ") || "Address not available"}
        </p>
      </div>
    </section>
  );
}

export default CompanyOverview;
