
import { useState } from "react";

function SearchBar({ onSearch, loading }) {
  const [companyName, setCompanyName] = useState("");

  function handleSubmit(event) {
    event.preventDefault();

    const trimmedName = companyName.trim();

    if (trimmedName) {
      onSearch(trimmedName);
    }
  }

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Enter company name (e.g. Microsoft)"
        value={companyName}
        onChange={(event) => setCompanyName(event.target.value)}
      />

      <button type="submit" disabled={loading || !companyName.trim()}>
        {loading ? "Searching..." : "Search Company"}
      </button>
    </form>
  );
}

export default SearchBar;
