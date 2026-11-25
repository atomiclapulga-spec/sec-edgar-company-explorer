import requests

url = "http://localhost:8000/api/companies/0000789019"
response = requests.get(url)
response.raise_for_status()

data = response.json()

print("Company:", data["company"]["company_name"])
print("Extraction method:", data["company_intelligence"]["extraction_method"])

for category in data["company_intelligence"]["categories"]:
    print("\n" + "=" * 90)
    print(category["category"], "|", category["status"])
    print("=" * 90)

    for finding in category["findings"]:
        if finding["evidence_type"] == "direct_disclosure":
            print(f"\nScore: {finding['relevance_score']}")
            print("Title:", finding["title"])
            print("Source section:", finding["source_section"])
            print("Matched keywords:", ", ".join(finding["matched_keywords"]))
            print("Evidence:")
            print(finding["description"])
