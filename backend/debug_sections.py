
import os
import requests
from dotenv import load_dotenv

from app.filing_extractor import clean_document, identify_item_markers

load_dotenv()

headers = {
    "User-Agent": os.getenv("SEC_USER_AGENT")
}

cik = "0000789019"

submissions_url = (
    f"https://data.sec.gov/submissions/CIK{cik}.json"
)

submissions = requests.get(
    submissions_url,
    headers=headers,
    timeout=30
).json()

recent = submissions["filings"]["recent"]

filing_index = next(
    i for i, form in enumerate(recent["form"])
    if form == "10-K"
)

accession = recent["accessionNumber"][filing_index]
document = recent["primaryDocument"][filing_index]

accession_clean = accession.replace("-", "")

filing_url = (
    f"https://www.sec.gov/Archives/edgar/data/"
    f"{int(cik)}/{accession_clean}/{document}"
)

response = requests.get(
    filing_url,
    headers=headers,
    timeout=60
)

response.raise_for_status()

html = response.content

lines = clean_document(html)
markers = identify_item_markers(lines)

print("\n========== ITEM 1 / ITEM 1A MARKERS ==========\n")

for marker in markers:
    if marker["part"] == "I" and marker["item"] in ["1", "1A"]:
        index = marker["index"]

        print(
            f"\nMarker: PART {marker['part']} "
            f"ITEM {marker['item']}"
        )
        print(f"Line index: {index}")

        print("Previous line:", lines[index - 1] if index > 0 else "")
        print("Following lines:")

        for line in lines[index + 1:index + 6]:
            print("  ", line[:200])

print("\n========== END DIAGNOSTIC ==========")
