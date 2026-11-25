import re
import os
import time
import threading

import json
from pathlib import Path

import requests

from functools import lru_cache
from contextlib import asynccontextmanager
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.filing_extractor import extract_10k_sections

from app.intelligence_extractor import (
    extract_company_intelligence,
    DATA_CATALOG,
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")

if not SEC_USER_AGENT or "your-email" in SEC_USER_AGENT.lower():
    raise RuntimeError(
        "Please configure SEC_USER_AGENT in your .env file."
    )

SEC_HEADERS = {
    "User-Agent": SEC_USER_AGENT,
    "Accept-Encoding": "gzip, deflate"
}

SEC_TICKER_URL = (
    "https://www.sec.gov/files/company_tickers_exchange.json"
)

SEC_SUBMISSIONS_URL = (
    "https://data.sec.gov/submissions/CIK{}.json"
)

SEC_FACTS_URL = (
    "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

REQUEST_INTERVAL = 0.12

_request_lock = threading.Lock()
_last_request_time = 0.0


def sec_request(url, return_text=False):
    """
    Make a paced request to SEC EDGAR.
    """

    global _last_request_time

    with _request_lock:

        elapsed = time.monotonic() - _last_request_time

        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)

        try:
            response = requests.get(
                url,
                headers=SEC_HEADERS,
                timeout=60
            )

            _last_request_time = time.monotonic()

            response.raise_for_status()

            if return_text:
                return response.content

            return response.json()

        except requests.exceptions.HTTPError as error:

            status_code = (
                response.status_code
                if "response" in locals()
                else None
            )

            if status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="SEC record or filing document not found."
                ) from error

            if status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="SEC rate limit reached. Please try again shortly."
                ) from error

            raise HTTPException(
                status_code=502,
                detail="SEC returned an HTTP error."
            ) from error

        except requests.exceptions.RequestException as error:
            raise HTTPException(
                status_code=502,
                detail="Unable to connect to SEC EDGAR."
            ) from error

        except ValueError as error:
            raise HTTPException(
                status_code=502,
                detail="SEC returned invalid JSON data."
            ) from error


def sec_get(url):
    return sec_request(url)


def sec_get_document(url):
    return sec_request(url, return_text=True)


# --------------------------------------------------
# COMPANY NAME SEARCH
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_company_mapping():

    data = sec_get(SEC_TICKER_URL)

    return data.get("data", [])


def normalize_name(name):

    return " ".join(
        name.lower()
        .replace(",", " ")
        .replace(".", " ")
        .split()
    )

# Verified company brand/name aliases.
# Keys and values use normalized company names.
COMPANY_ALIASES = {
    "google": "alphabet inc",
}

def search_companies(name):

    search_name = normalize_name(name)

    if not search_name:
        return []

    records = get_company_mapping()

    # Resolve a verified brand alias to its SEC legal company name.
    alias_target = COMPANY_ALIASES.get(search_name)

    search_terms = [search_name]

    if alias_target:
        search_terms.append(alias_target)

    # Store results by CIK to avoid duplicate share-class entries.
    unique_matches = {}

    for record in records:

        if len(record) < 4:
            continue

        cik, company_name, ticker, exchange = record

        normalized_company = normalize_name(company_name)

        score = 0

        for term in search_terms:

            if normalized_company == term:

                current_score = 100

            elif normalized_company.startswith(term):

                current_score = 80

            elif term in normalized_company:

                current_score = 60

            else:

                current_score = 0

            # Exact alias resolution receives a score below
            # an exact legal company-name match.
            if alias_target and term == alias_target:
                current_score = min(current_score, 95)

            score = max(score, current_score)

        if score == 0:
            continue

        cik = str(cik).zfill(10)

        result = {
            "cik": cik,
            "company_name": company_name,
            "ticker": ticker,
            "exchange": exchange,
            "match_score": score
        }

        existing = unique_matches.get(cik)

        if existing is None or score > existing["match_score"]:

            unique_matches[cik] = result

    matches = list(unique_matches.values())

    matches.sort(
        key=lambda item: (
            -item["match_score"],
            item["company_name"]
        )
    )

    return matches[:15]


# --------------------------------------------------
# FINANCIAL METRIC DEFINITIONS
# --------------------------------------------------

FINANCIAL_METRICS = {
    "Revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet"
    ],
    "Operating Income": [
        "OperatingIncomeLoss"
    ],
    "Net Income": [
        "NetIncomeLoss",
        "ProfitLoss"
    ],
    "Total Assets": [
        "Assets"
    ],
    "Total Liabilities": [
        "Liabilities"
    ],
    "Cash and Cash Equivalents": [
        "CashAndCashEquivalentsAtCarryingValue"
    ],
    "Stockholders Equity": [
        "StockholdersEquity"
    ]
}

INSTANT_METRICS = {
    "Total Assets",
    "Total Liabilities",
    "Cash and Cash Equivalents",
    "Stockholders Equity"
}


# --------------------------------------------------
# FINANCIAL PERIOD CLASSIFICATION
# --------------------------------------------------

def calculate_duration_days(item):

    start = item.get("start")
    end = item.get("end")

    if not start or not end:
        return None

    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)

        return (end_date - start_date).days + 1

    except (ValueError, TypeError):
        return None


def classify_financial_period(item, metric_name):

    """
    Classify XBRL facts by their reporting duration.

    Instant facts:
        Balance-sheet values with no start date.

    Quarterly:
        Approximately three-month reporting periods.

    Year-to-date:
        Multi-month periods shorter than a full financial year.

    Annual:
        Approximately twelve-month reporting periods.

    Unclassified:
        Periods that do not fit these rules.
    """

    if metric_name in INSTANT_METRICS and not item.get("start"):
        return "point_in_time"

    if not item.get("start"):
        return "point_in_time"

    duration = calculate_duration_days(item)

    if duration is None:
        return "unclassified"

    if 70 <= duration <= 110:
        return "quarterly"

    if 150 <= duration <= 300:
        return "year_to_date"

    if 330 <= duration <= 380:
        return "annual"

    return "unclassified"


def get_fact_unit(concept):

    units = concept.get("units", {})

    if "USD" in units:
        return "USD", units["USD"]

    if "pure" in units:
        return "pure", units["pure"]

    return None, []


def deduplicate_facts(items, metric_name):

    """
    Keep the most recently filed version of each reported period.
    """

    latest_by_period = {}

    for item in items:

        period_key = (
            item.get("start"),
            item.get("end")
        )

        existing = latest_by_period.get(period_key)

        if existing is None:
            latest_by_period[period_key] = item
            continue

        if item.get("filed", "") > existing.get("filed", ""):
            latest_by_period[period_key] = item

    return list(latest_by_period.values())


def format_financial_fact(item, metric_name, unit_name, tag):

    return {
        "start": item.get("start"),
        "end": item.get("end"),
        "value": item.get("val"),
        "unit": unit_name,
        "filed": item.get("filed"),
        "form": item.get("form"),
        "period_type": classify_financial_period(
            item,
            metric_name
        ),
        "xbrl_tag": tag,
        "frame": item.get("frame")
    }



def extract_financial_metric(facts, metric_name, tags):

    concepts = facts.get("facts", {}).get(
        "us-gaap",
        {}
    )

    # Collect records from ALL available XBRL tags.
    classified = {
        "quarterly": [],
        "year_to_date": [],
        "annual": [],
        "point_in_time": [],
        "unclassified": []
    }

    for tag in tags:

        concept = concepts.get(tag)

        if not concept:
            continue

        unit_name, values = get_fact_unit(concept)

        if not values:
            continue

        relevant = [
            item for item in values
            if item.get("form") in ["10-K", "10-Q"]
            and item.get("end")
            and item.get("filed")
        ]

        if not relevant:
            continue

        # Remove duplicate filings within this XBRL tag.
        relevant = deduplicate_facts(
            relevant,
            metric_name
        )

        for item in relevant:

            period_type = classify_financial_period(
                item,
                metric_name
            )

            formatted = format_financial_fact(
                item,
                metric_name,
                unit_name,
                tag
            )

            classified[period_type].append(formatted)

    # Sort each period group using reporting end date,
    # followed by filing date.
    for group in classified.values():

        group.sort(
            key=lambda item: (
                item.get("end") or "",
                item.get("filed") or ""
            ),
            reverse=True
        )

    # Balance-sheet metrics use the latest instant fact.
    if metric_name in INSTANT_METRICS:

        preferred_history = classified["point_in_time"]

    else:

        # Prefer the latest standalone quarter.
        # Fall back to annual, YTD, and unclassified data.
        preferred_history = (
            classified["quarterly"]
            or classified["annual"]
            or classified["year_to_date"]
            or classified["unclassified"]
        )

    latest = (
        preferred_history[0]
        if preferred_history
        else None
    )

    # Retain the existing history structure for frontend compatibility.
    all_history = []

    for group in [
        "quarterly",
        "year_to_date",
        "annual",
        "point_in_time",
        "unclassified"
    ]:
        all_history.extend(classified[group])

    return {
        "metric": metric_name,
        "value": latest.get("value") if latest else None,
        "unit": latest.get("unit") if latest else None,
        "period_start": latest.get("start") if latest else None,
        "period_end": latest.get("end") if latest else None,
        "filing_date": latest.get("filed") if latest else None,
        "form": latest.get("form") if latest else None,
        "period_type": latest.get("period_type") if latest else None,
        "xbrl_tag": latest.get("xbrl_tag") if latest else None,

        # Retain history for compatibility with the existing frontend.
        "history": all_history[:50],

        # Explicitly separated histories.
        "quarterly_history": classified["quarterly"][:20],
        "year_to_date_history": classified["year_to_date"][:20],
        "annual_history": classified["annual"][:20],
        "point_in_time_history": classified["point_in_time"][:20],
        "unclassified_history": classified["unclassified"][:20]
    }

def extract_financials(facts):

    results = {}

    for metric_name, tags in FINANCIAL_METRICS.items():

        results[metric_name] = extract_financial_metric(
            facts,
            metric_name,
            tags
        )

    return results


# --------------------------------------------------
# FILING HISTORY
# --------------------------------------------------

def extract_filings(submissions, cik):

    recent = submissions.get(
        "filings", {}
    ).get("recent", {})

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    documents = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])

    filings = []

    count = min(
        30,
        len(forms),
        len(dates),
        len(accession_numbers),
        len(documents)
    )

    for index in range(count):

        accession = accession_numbers[index]
        document = documents[index]

        accession_clean = accession.replace("-", "")

        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik)}/{accession_clean}/{document}"
        )

        filings.append({
            "form": forms[index],
            "filing_date": dates[index],
            "report_date": (
                report_dates[index]
                if index < len(report_dates)
                else None
            ),
            "accession_number": accession,
            "primary_document": document,
            "url": filing_url
        })

    return filings


# --------------------------------------------------
# LATEST 10-K EXTRACTION
# --------------------------------------------------

def extract_latest_10k(submissions, cik):

    recent = submissions.get(
        "filings", {}
    ).get("recent", {})

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    documents = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])

    for index, form in enumerate(forms):

        if form != "10-K":
            continue

        if (
            index >= len(accessions)
            or index >= len(documents)
        ):
            continue

        accession = accessions[index]
        document = documents[index]

        accession_clean = accession.replace("-", "")

        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{int(cik)}/{accession_clean}/{document}"
        )

        html = sec_get_document(filing_url)

        sections = extract_10k_sections(html)
        debug_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "debug_business_overview.txt"
        )

        os.makedirs(os.path.dirname(debug_path), exist_ok=True)

        with open(debug_path, "w", encoding="utf-8") as debug_file:
            debug_file.write(
                sections.get("business_overview", {}).get("content") or ""
            )

        print(
            "Business Overview saved:",
            len(sections.get("business_overview", {}).get("content") or ""),
            "characters"
        )

        filing_date = (
            dates[index]
            if index < len(dates)
            else None
        )

        report_date = (
            report_dates[index]
            if index < len(report_dates)
            else None
        )

        available_count = sum(
            1 for section in sections.values()
            if section.get("available")
        )

        return {
            "available": True,
            "form": "10-K",
            "filing_date": filing_date,
            "report_date": report_date,
            "accession_number": accession,
            "document_url": filing_url,
            "sections": sections,
            "extraction_summary": {
                "total_sections_checked": len(sections),
                "sections_available": available_count
            }
        }

    return {
        "available": False,
        "message": "No recent 10-K filing was found.",
        "sections": {}
    }


# --------------------------------------------------
# RETRIEVED DATA CATEGORY SUMMARY
# --------------------------------------------------

def build_retrieved_categories(
    company,
    financials,
    filings,
    business_information,
    sources
):

    categories = []

    # Company profile
    company_items = []

    company_fields = {
        "company_name": "Company name",
        "cik": "CIK",
        "tickers": "Ticker",
        "exchanges": "Exchange",
        "sic": "SIC code",
        "sic_description": "Industry description",
        "fiscal_year_end": "Fiscal year end",
        "former_names": "Former company names",
        "business_address": "Business address",
        "mailing_address": "Mailing address"
    }

    for field, label in company_fields.items():

        value = company.get(field)

        if value not in (None, "", [], {}):
            company_items.append(label)

    categories.append({
        "category": "Company Profile",
        "status": (
            "retrieved"
            if company_items
            else "unavailable"
        ),
        "items": company_items,
        "source": sources["submissions"]
    })

    # Financial information
    financial_items = []

    for metric_name, metric in financials.items():

        if metric.get("value") is not None:
            financial_items.append(metric_name)

    financial_status = (
        "retrieved"
        if financial_items
        else "unavailable"
    )

    categories.append({
        "category": "Financial Information",
        "status": financial_status,
        "items": financial_items,
        "source": sources["company_facts"]
    })

    # Filing history
    filing_types = sorted({
        filing.get("form")
        for filing in filings
        if filing.get("form")
    })

    categories.append({
        "category": "SEC Filing History",
        "status": (
            "retrieved"
            if filings
            else "unavailable"
        ),
        "items": filing_types,
        "source": "SEC submissions API"
    })

    # Individual 10-K sections
    sections = business_information.get("sections", {})

    section_category_names = {
        "business_overview": "Business Overview",
        "risk_factors": "Risk Factors",
        "management_discussion": (
            "Management Discussion and Analysis"
        ),
        "workforce_information": "Workforce Disclosures"
    }

    for key, category_name in section_category_names.items():

        section = sections.get(key, {})
        available = bool(section.get("available"))
        content = section.get("content")

        if available and content:

            status = "retrieved"
            items = [section.get("title", category_name)]

        elif business_information.get("available"):

            status = "unavailable"
            items = []

        else:

            status = "unavailable"
            items = []

        categories.append({
            "category": category_name,
            "status": status,
            "items": items,
            "source": business_information.get("document_url"),
            "filing_date": business_information.get("filing_date"),
            "form": business_information.get("form")
        })

    # Overall filing section extraction status
    checked = bool(business_information.get("available"))

    available_sections = [
        key for key, section in sections.items()
        if section.get("available")
    ]

    if not checked:
        section_status = "unavailable"
    elif available_sections:
        if len(available_sections) == len(sections):
            section_status = "retrieved"
        else:
            section_status = "partially_retrieved"
    else:
        section_status = "unavailable"

    categories.append({
        "category": "10-K Filing Sections",
        "status": section_status,
        "items": [
            section_category_names.get(key, key)
            for key in available_sections
        ],
        "source": business_information.get("document_url"),
        "filing_date": business_information.get("filing_date")
    })

    return categories


# --------------------------------------------------
# COMPANY PROFILE
# --------------------------------------------------




def build_change_management_export(company_profile):

    company = company_profile.get("company", {})
    financials = company_profile.get("financials", {})
    intelligence = company_profile.get("company_intelligence", {})

    def make_key(name):
        return (
            str(name)
            .strip()
            .lower()
            .replace("&", "and")
            .replace("/", "_")
            .replace("-", "_")
            .replace(" ", "_")
        )

    def has_useful_value(value):
        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, dict)):
            return len(value) > 0

        return True

    
    
    def structure_product_services(descriptions):
        """
        Convert disclosed product/service descriptions into
        named entries with descriptive points.

        Preserve source wording and keep explanations attached
        to the products or services they describe.
        """

        structured = []

        if not isinstance(descriptions, list):
            return descriptions

        for description in descriptions:

            if not isinstance(description, str):
                continue

            description = " ".join(description.split()).strip()

            if not description:
                continue

                        # Derive the name from the opening phrase.
            if ":" in description:
                name, separator, details = description.partition(":")
            else:
                name, separator, details = description.partition(",")

            name = name.strip()
            details = details.strip() if separator else ""

            points = []

            if details:
                raw_points = re.split(
                    r";\s*(?:and\s+)?",
                    details,
                    flags=re.IGNORECASE
                )

                for point in raw_points:
                    point = point.strip(" ;,")

                    if not point:
                        continue

                    point = re.sub(
                        r"^(?:and\s+)?(?:including|comprising)\s+",
                        "",
                        point,
                        flags=re.IGNORECASE
                    )

                    if point:
                        device_parts = re.split(
                            r"\s+and\s+(?=Devices,\s+comprising\b)",
                            point,
                            flags=re.IGNORECASE
                        )

                        for part in device_parts:
                            part = part.strip()

                            if not part:
                                continue

                            part = re.sub(
                                r"^on-premises\b",
                                "On-premises",
                                part,
                                flags=re.IGNORECASE
                            )

                            points.append(part)

            structured.append({
                "name": name,
                "points": points
            })

        return structured


    
    # COMPANY INFORMATION

    clean_company = {
        "company_name": company.get("company_name"),
        "cik": company.get("cik"),
        "tickers": company.get("tickers", []),
        "exchanges": company.get("exchanges", []),
        "industry": company.get("sic_description"),
        "business_address": company.get("business_address")
    }

    clean_company = {
        key: value
        for key, value in clean_company.items()
        if has_useful_value(value)
    }

    # FINANCIAL INFORMATION

    clean_financials = {}

    for metric_name, metric in financials.items():

        if not isinstance(metric, dict):
            continue

        value = metric.get("value")

        if not has_useful_value(value):
            continue

        clean_financials[make_key(metric_name)] = {
            "value": value,
            "unit": metric.get("unit"),
            "reporting_period": metric.get("period_end")
        }

    # ORGANISATIONAL INTELLIGENCE

    clean_categories = {}

    # Index the extracted categories and items for quick lookup.
    extracted_categories = {}

    for category in intelligence.get("categories", []):
        department = category.get("department")

        if not department:
            continue

        department_key = make_key(department)

        extracted_items = {}

        for item in category.get("data_items", []):
            item_name = item.get("name")

            if item_name:
                extracted_items[make_key(item_name)] = item

        extracted_categories[department_key] = extracted_items


    # Build every organisational category from the canonical catalog.
    # Finance & Accounting remains in financial_information.
    for department, definition in DATA_CATALOG.items():

        if department == "Finance & Accounting":
            continue

        department_key = make_key(department)

        clean_items = {}
        extracted_items = extracted_categories.get(
            department_key, {}
        )

        for item_name in definition.get("items", {}):

            item_key = make_key(item_name)

            # Default for information not found in SEC filings.
            clean_item = {
                "status": "not_found",
                "value": None,
            }

            extracted_item = extracted_items.get(item_key)

            if extracted_item:

                extraction_status = extracted_item.get(
                    "extraction_status",
                    "not_found"
                )

                extracted_value = extracted_item.get(
                    "extracted_value"
                )

                unit = extracted_item.get("unit")

                # Handle extracted values that contain value/unit metadata.
                if isinstance(extracted_value, dict):
                    if "value" in extracted_value:
                        value = extracted_value.get("value")

                        if extracted_value.get("unit") is not None:
                            unit = extracted_value.get("unit")
                    else:
                        value = extracted_value
                else:
                    value = extracted_value

                if extraction_status == "mentioned":

                    clean_item = {
                        "status": "mentioned",
                        "value": None,
                    }

                    reporting_period = (
                        extracted_item.get("reporting_period")
                        or extracted_item.get("period_end")
                    )

                    if reporting_period is not None:
                        clean_item["reporting_period"] = reporting_period

                elif has_useful_value(value):

                    clean_item = {
                        "status": (
                            extraction_status
                            if extraction_status != "not_found"
                            else "disclosed"
                        ),
                        "value": value,
                    }

                    if unit is not None:
                        clean_item["unit"] = unit

                    reporting_period = (
                        extracted_item.get("reporting_period")
                        or extracted_item.get("period_end")
                    )

                    if reporting_period is not None:
                        clean_item["reporting_period"] = reporting_period

                    # Preserve the existing product/service transformation.
                    if item_key == "products_and_services":
                        clean_item["value"] = (
                            structure_product_services(value)
                        )

                # If no useful value was extracted, retain the default:
                # status = not_found, value = None.

            clean_items[item_key] = clean_item

        # Include the category even when every item is not_found.
        clean_categories[department_key] = clean_items

    return {
        "company": clean_company,
        "financial_information": clean_financials,
        "organisational_intelligence": {
            "summary": intelligence.get("summary", {}),
            **clean_categories
        },
        "data_source": "SEC EDGAR"
    }



def get_company_profile(cik):

    cik = str(cik).zfill(10)

    submissions_url = SEC_SUBMISSIONS_URL.format(cik)
    facts_url = SEC_FACTS_URL.format(cik)

    submissions = sec_get(submissions_url)
    facts = sec_get(facts_url)

    recent_filings = extract_filings(
        submissions,
        cik
    )

    financials = extract_financials(facts)

    business_information = extract_latest_10k(
        submissions,
        cik
    )

    company_intelligence = extract_company_intelligence(
        business_information,
        financials
    )

    company = {
        "company_name": submissions.get("name"),
        "cik": cik,
        "tickers": submissions.get("tickers", []),
        "exchanges": submissions.get("exchanges", []),
        "sic": submissions.get("sic"),
        "sic_description": submissions.get("sicDescription"),
        "fiscal_year_end": submissions.get("fiscalYearEnd"),
        "former_names": submissions.get("formerNames", []),
        "business_address": submissions.get(
            "addresses", {}
        ).get("business", {}),
        "mailing_address": submissions.get(
            "addresses", {}
        ).get("mailing", {})
    }

    sources = {
        "submissions": submissions_url,
        "company_facts": facts_url
    }

    retrieved_categories = build_retrieved_categories(
        company,
        financials,
        recent_filings,
        business_information,
        sources
    )

    # Assemble the complete company profile
    company_profile = {
        "company": company,
        "financials": financials,
        "business_information": business_information,
        "company_intelligence": company_intelligence,
        "filings": recent_filings,
        "retrieved_categories": retrieved_categories,
        "sources": sources
    }

    # Save JSON in the project root
    project_root = Path(__file__).resolve().parents[2]

    output_directory = (
        project_root / "data" / "company_profiles"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_directory / f"{cik}.json"

    clean_profile = build_change_management_export(
    company_profile
)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            clean_profile,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Clean company profile saved: {output_file}")

    print(f"Company profile saved: {output_file}")

    return company_profile


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("Company Information Explorer backend started.")

    yield

    print("Backend shutting down.")


app = FastAPI(
    title="Company Information Explorer API",
    description="Retrieve public company information from SEC EDGAR.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def root():

    return {
        "message": "Company Information Explorer API is running."
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/api/companies/search")
def company_search(name: str = Query(min_length=1)):

    matches = search_companies(name)

    return {
        "query": name,
        "total_matches": len(matches),
        "matches": matches
    }


@app.get("/api/companies/{cik}")
def company_details(cik: str):

    if not cik.isdigit() or len(cik) > 10:

        raise HTTPException(
            status_code=400,
            detail="Please provide a valid numeric CIK."
        )

    return get_company_profile(cik)
