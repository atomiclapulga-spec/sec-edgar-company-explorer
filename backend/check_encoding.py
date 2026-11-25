
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

headers = {
    "User-Agent": os.getenv("SEC_USER_AGENT")
}

cik = "0000789019"

submissions = requests.get(
    f"https://data.sec.gov/submissions/CIK{cik}.json",
    headers=headers,
    timeout=30
).json()

recent = submissions["filings"]["recent"]

index = next(
    i for i, form in enumerate(recent["form"])
    if form == "10-K"
)

accession = recent["accessionNumber"][index].replace("-", "")
document = recent["primaryDocument"][index]

url = (
    f"https://www.sec.gov/Archives/edgar/data/"
    f"{int(cik)}/{accession}/{document}"
)

response = requests.get(url, headers=headers, timeout=60)
response.raise_for_status()

print("HTTP encoding:", response.encoding)
print("Detected encoding:", response.apparent_encoding)

# Parse the original bytes.
soup = BeautifulSoup(response.content, "html.parser")

for element in soup([
    "script",
    "style",
    "ix:header",
    "ix:hidden",
]):
    element.decompose()

text = soup.get_text(separator="\n", strip=True)

print("\n========== RAW BYTE CHECK ==========")

position = response.content.find(b"customers")

if position != -1:
    print(repr(response.content[position:position + 150]))
else:
    print("The word 'customers' was not found in the raw bytes.")

print("\n========== EXTRACTED TEXT CHECK ==========")

for line in text.splitlines():
    if "customers" in line.lower() and "multi-cloud" in line.lower():
        print("Text:", repr(line))

        print("Character codes:")
        print([
            hex(ord(character))
            for character in line
            if ord(character) > 127
        ])
        break

print("\n========== MANAGEMENT HEADING CHECK ==========")

for line in text.splitlines():
    if "management" in line.lower() and "discussion" in line.lower():
        print(repr(line))
        break
