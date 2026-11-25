
import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

CIK = "0000789019"
USER_AGENT = os.getenv("SEC_USER_AGENT")

if not USER_AGENT:
    raise RuntimeError("SEC_USER_AGENT is missing from backend/.env")

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}

print("Fetching SEC submissions...")

submissions_url = (
    f"https://data.sec.gov/submissions/CIK{CIK}.json"
)

response = requests.get(
    submissions_url,
    headers=HEADERS,
    timeout=30
)
response.raise_for_status()

submissions = response.json()
recent = submissions["filings"]["recent"]

filing_index = next(
    (
        i for i, form in enumerate(recent["form"])
        if form == "10-K"
    ),
    None
)

if filing_index is None:
    raise RuntimeError("No recent 10-K filing found.")

accession = recent["accessionNumber"][filing_index]
primary_document = recent["primaryDocument"][filing_index]
filing_date = recent["filingDate"][filing_index]

accession_clean = accession.replace("-", "")

document_url = (
    f"https://www.sec.gov/Archives/edgar/data/"
    f"{int(CIK)}/{accession_clean}/{primary_document}"
)

print(f"\nLatest 10-K filing: {filing_date}")
print(f"Document: {primary_document}")
print("Downloading filing...\n")

document_headers = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
}

response = requests.get(
    document_url,
    headers=document_headers,
    timeout=60
)
response.raise_for_status()

# Pass bytes to BeautifulSoup so it can detect the document encoding.
soup = BeautifulSoup(response.content, "html.parser")

for element in soup(["script", "style", "ix:header", "ix:hidden"]):
    element.decompose()

lines = []

for line in soup.get_text(separator="\n").splitlines():
    line = re.sub(r"\s+", " ", line).strip()
    if line:
        lines.append(line)

print("=" * 75)
print("LINES CONTAINING ITEM REFERENCES")
print("=" * 75)

matches = [
    i for i, line in enumerate(lines)
    if re.search(r"\bITEM\s+(?:1A?|7)\b", line, re.IGNORECASE)
]

printed = set()

for index in matches:
    start = max(0, index - 2)
    end = min(len(lines), index + 4)

    if any(i in printed for i in range(start, end)):
        continue

    print(f"\n--- Around line {index + 1} ---")

    for i in range(start, end):
        print(f"{i + 1}: {lines[i]}")
        printed.add(i)

    if len(printed) > 250:
        print("\nOutput limit reached.")
        break

print("\n" + "=" * 75)
print("LINES CONTAINING BUSINESS / RISK FACTORS")
print("=" * 75)

count = 0

for index, line in enumerate(lines):
    if re.search(
        r"\bBUSINESS\b|\bRISK FACTORS\b",
        line,
        re.IGNORECASE
    ):
        print(f"{index + 1}: {line[:300]}")
        count += 1

        if count >= 40:
            break

print("\nDiagnostic complete.")
