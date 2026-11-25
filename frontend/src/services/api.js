
const API_BASE_URL = "http://localhost:8000";

export async function searchCompanies(companyName) {
  const response = await fetch(
    `${API_BASE_URL}/api/companies/search?name=${encodeURIComponent(companyName)}`
  );

  if (!response.ok) {
    throw new Error("Unable to search for companies.");
  }

  return response.json();
}

export async function getCompanyProfile(cik) {
  const response = await fetch(
    `${API_BASE_URL}/api/companies/${encodeURIComponent(cik)}`
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Unable to retrieve company information.");
  }

  return response.json();
}
