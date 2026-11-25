
import { useState } from "react";

import SearchBar from "./components/SearchBar";
import CompanyOverview from "./components/CompanyOverview";
import FinancialOverview from "./components/FinancialOverview";
import CompanyIntelligence from "./components/CompanyIntelligence";
import FilingsTable from "./components/FilingsTable";

import { searchCompanies, getCompanyProfile } from "./services/api";

import "./App.css";

function App() {
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [companyData, setCompanyData] = useState(null);
  const [error, setError] = useState("");
  const [searchedName, setSearchedName] = useState("");

  async function handleSearch(companyName) {
    setLoading(true);
    setError("");
    setCompanyData(null);
    setSearchResults([]);
    setSearchedName(companyName);

    try {
      const searchData = await searchCompanies(companyName);

      if (!searchData.matches || searchData.matches.length === 0) {
        setError("No matching companies found in the SEC database.");
        return;
      }

      setSearchResults(searchData.matches);

      // Automatically load the highest-ranked company match.
      await loadCompanyProfile(searchData.matches[0].cik);
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function loadCompanyProfile(cik) {
    setLoading(true);
    setError("");

    try {
      const profile = await getCompanyProfile(cik);
      setCompanyData(profile);
    } catch (err) {
      setError(err.message || "Unable to load company information.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-content">
          <p className="eyebrow">SEC EDGAR DATA EXPLORER</p>

          <h1>Company Information Explorer</h1>

          <p className="hero-description">
            Explore publicly available company information,
            financial data and regulatory filings.
          </p>

          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>
      </header>

      <main className="main-content">
        {searchedName && (
          <p className="search-caption">
            Search results for: <strong>{searchedName}</strong>
          </p>
        )}

        {error && <div className="error-message">{error}</div>}

        {loading && (
          <div className="loading-message">
            Retrieving company information from SEC EDGAR...
          </div>
        )}

        {searchResults.length > 1 && (
          <section className="section">
            <h2>Matching Companies</h2>

            <div className="matches-list">
              {searchResults.map((company) => (
                <button
                  className={`match-button ${
                    companyData?.company?.cik === company.cik
                      ? "selected"
                      : ""
                  }`}
                  key={company.cik}
                  onClick={() => loadCompanyProfile(company.cik)}
                  disabled={loading}
                >
                  <span>{company.company_name}</span>
                  <small>
                    {company.ticker || "No ticker"} · CIK {company.cik}
                  </small>
                </button>
              ))}
            </div>
          </section>
        )}

        {companyData && (
          <>
            <div className="company-heading">
              <div>
                <p className="eyebrow">COMPANY PROFILE</p>
                <h2>{companyData.company.company_name}</h2>
                <p>
                  {companyData.company.tickers?.join(", ") || "No ticker"}
                  {" · "}
                  {companyData.company.exchanges?.join(", ") || "No exchange"}
                </p>
              </div>

              <span className="source-label">SEC EDGAR</span>
            </div>

            <CompanyOverview company={companyData.company} />

            <FinancialOverview
              financials={companyData.financials}
            />

            <CompanyIntelligence
              intelligence={companyData.company_intelligence}
            />

            <FilingsTable filings={companyData.filings} />

            <p className="data-disclaimer">
              Information sourced from public SEC EDGAR submissions
              and company facts. Financial figures are shown with their
              reported periods and filing dates. Company data availability
              reflects information identified in the retrieved SEC sources;
              it does not represent a complete internal company inventory.
              Always refer to the original SEC filing for authoritative
              information.
            </p>
          </>
        )}

        {!companyData && !loading && !error && (
          <div className="empty-state">
            <h2>Start by searching for a company</h2>
            <p>
              Enter a US public company's name above to explore its
              SEC registration details, financial information and filings.
            </p>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Company Information Explorer · Powered by SEC EDGAR</p>
      </footer>
    </div>
  );
}

export default App;
