
import requests

url = "http://localhost:8000/api/companies/0000789019"

response = requests.get(url, timeout=120)
response.raise_for_status()

print("Content-Type:", response.headers.get("Content-Type"))

data = response.json()

business = data["business_information"]["sections"]["business_overview"]["content"]
management = data["business_information"]["sections"]["management_discussion"]["content"]

print("\n========== BUSINESS OVERVIEW ==========")
for line in business.splitlines():
    if "customers" in line.lower() and "multi-cloud" in line.lower():
        print(repr(line))
        break

print("\n========== MANAGEMENT DISCUSSION ==========")
for line in management.splitlines():
    if "management" in line.lower() and "discussion" in line.lower():
        print(repr(line))
        break

print("\n========== UNICODE CHECK ==========")
print("Correct apostrophe present:", "\u2019" in business)
print("Corrupted sequence present:", "â" in business)
