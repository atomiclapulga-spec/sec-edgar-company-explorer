
import requests

# Replace with your actual contact email
SEC_USER_AGENT = "CompanyInformationExplorer contact your-atomiclapulga@gmail.com"

headers = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate"
}

cik = "0000789019"

url = f"https://data.sec.gov/submissions/CIK{cik}.json"

try:
    print("Connecting to SEC EDGAR...")

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print("\n========== SEC CONNECTION SUCCESS ==========")

    print("Company Name:", data.get("name"))
    print("CIK:", data.get("cik"))
    print("Tickers:", data.get("tickers"))
    print("Exchanges:", data.get("exchanges"))

    print("\n========== FORMER COMPANY NAMES ==========")

    for item in data.get("formerNames", []):
        print(item.get("name"))

    print("\n========== RECENT FILINGS ==========")

    recent = data.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])

    for i in range(min(5, len(forms))):
        print(f"Form: {forms[i]} | Date: {dates[i]}")

except requests.exceptions.RequestException as error:
    print("\nSEC API request failed:", error)
