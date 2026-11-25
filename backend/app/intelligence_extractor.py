
import re
import time

# ============================================================
# 1. COMPANY INFORMATION CATALOG
# ============================================================

DATA_CATALOG = {
    "Finance & Accounting": {
        "type": "financial",
        "items": {
            "Revenue": ["Revenue"],
            "Operating income": ["Operating Income"],
            "Net income": ["Net Income"],
            "Operating expenses": ["Operating Expenses"],
            "Total assets": ["Total Assets"],
            "Total liabilities": ["Total Liabilities"],
            "Cash and cash equivalents": ["Cash and Cash Equivalents"],
            "Stockholders' equity": ["Stockholders Equity"],
        },
    },

    "Human Resources": {
        "type": "filing",
        "sections": ["business_overview", "management_discussion"],
        "items": {
            "Total employee count": [
                "employed approximately",
                "number of employees",
                "employees worldwide",
            ],
            "Domestic and international workforce": [
                "employees in the u.s.",
                "employees internationally",
                "internationally and",
                "in the u.s. and",
            ],
            "Employee distribution by function": [
                "employees were in operations",
                "were in product research and development",
                "were in sales and marketing",
                "general and administration",
            ],
            "Employee compensation": [
                "total compensation offering",
                "employee compensation",
                "compensation and benefits",
            ],
            "Employee benefits": [
                "benefits package",
                "employee benefits",
                "health and welfare benefits",
            ],
            "Employee development and training": [
                "employee development",
                "continuous learning",
                "talent development",
                "professional growth",
            ],
            "Employee wellbeing": [
                "employee wellbeing",
                "employee well-being",
                "wellness programs",
            ],
            "Collective bargaining": [
                "collective bargaining agreements",
                "collective bargaining",
            ],
            "Employee engagement": [
                "employee engagement",
                "employee listening systems",
                "employee feedback",
            ],
        },
    },

    "IT & Technology": {
        "type": "filing",
        "sections": [
            "business_overview",
            "risk_factors",
            "management_discussion",
        ],
        "items": {
            "Datacenter infrastructure": [
                "datacenters",
                "data centers",
            ],
            "Cloud infrastructure and services": [
                "cloud infrastructure",
                "cloud computing",
                "cloud services",
            ],
            "Server and computing capacity": [
                "server capacity",
                "computing power",
                "computing capacity",
            ],
            "Artificial intelligence technology": [
                "artificial intelligence",
                "generative ai",
                "ai infrastructure",
            ],
            "Networking infrastructure": [
                "network infrastructure",
                "networking supplies",
            ],
            "Technology systems and platforms": [
                "information systems",
                "technology infrastructure",
                "digital infrastructure",
            ],
            "Cybersecurity and information security": [
                "cybersecurity",
                "information security",
                "security incidents",
            ],
            "Third-party technology dependencies": [
                "third-party providers",
                "cloud infrastructure providers",
                "technology providers",
            ],
        },
    },

    "Operations & Supply Chain": {
        "type": "filing",
        "sections": [
            "business_overview",
            "risk_factors",
            "management_discussion",
        ],
        "items": {
            "Manufacturing activities": [
                "manufacturing facilities",
                "manufacturing operations",
                "manufacture devices",
                "manufacturing activities",
            ],
            "Third-party manufacturers": [
                "third-party manufacturers",
                "third party manufacturers",
                "contract manufacturers",
            ],
            "Supplier dependencies": [
                "qualified suppliers",
                "critical suppliers",
                "supplier capacity",
                "supplier disruptions",
            ],
            "Vendor management": [
                "vendor management",
                "third-party vendors",
                "vendor relationships",
            ],
            "Logistics and distribution": [
                "logistics",
                "distribution operations",
                "transportation",
            ],
            "Supply chain efficiency and resilience": [
                "supply chain efficiency",
                "supply chain resilience",
                "supply chain disruptions",
            ],
            "Global operations centres": [
                "global operations service center",
                "global operations center",
                "operations service center",
            ],
            "Business continuity": [
                "business continuity",
                "continuity of operations",
                "critical business functions",
            ],
        },
    },

    "Sales & Marketing": {
        "type": "filing",
        "sections": ["business_overview", "management_discussion"],
        "items": {
            "Direct sales channels": [
                "direct sales activities",
                "direct sales channels",
            ],
            "Indirect sales channels": [
                "indirect sales activities",
                "indirect sales channels",
            ],
            "Distribution channels": [
                "distribution channels",
                "distribution network",
                "direct sales activities",
                "direct sales channels",
                "indirect sales activities",
                "indirect sales channels",
            ],
            "Partner network": [
                "network of partners",
                "partner network",
                "channel partners",
            ],
            "Sales and marketing expenses": [
                "sales and marketing expenses",
            ],
            "Advertising and promotional expenses": [
                "advertising expenses",
                "advertising and promotional",
                "marketing campaigns",
            ],
            "Customer-facing commercial activities": [
                "serve customers",
                "customer relationships",
                "customer engagement",
            ],
        },
    },

    "Business Structure & Products": {
        "type": "filing",
        "sections": ["business_overview", "management_discussion"],
        "items": {
            "Reportable business segments": [
                "reportable segment",
                "reportable segments",
                "segment consists of",
            ],
            "Products and services": [
                "products and services",
                "product portfolio",
                "services portfolio",
            ],
            "Business models": [
                "business model",
                "business models",
            ],
            "Operating segments": [
                "operating segment",
                "operating segments",
            ],
            "Business segment descriptions": [
                "our productivity and business processes segment",
                "our intelligent cloud segment",
                "our more personal computing segment",
            ],
        },
    },

    "Geographic Operations": {
        "type": "filing",
        "sections": [
            "business_overview",
            "risk_factors",
            "management_discussion",
        ],
        "items": {
            "International operations": [
                "international operations",
                "operations outside the united states",
            ],
            "Geographic markets and regions": [
                "geographic regions",
                "international markets",
                "foreign markets",
                "asia pacific",
            ],
            "Foreign currency exposure": [
                "foreign currency",
                "foreign exchange rates",
                "currency fluctuations",
            ],
            "Cross-border data transfers": [
                "cross-border",
                "across national boundaries",
                "transfer of personal data globally",
            ],
            "Regional regulatory requirements": [
                "regional regulatory",
                "regulations in the eu",
                "regulatory requirements in",
                "european union",
                "eu member state laws",
                "eu general data protection regulation",
                "general data protection regulation",
                "data protection authorities",
                "foreign competition laws",
                "competition laws and regulations",
                "regulations in the united kingdom",
                "regulations in china",
                "foreign jurisdictions",
                "local tax authorities",
                "multiple jurisdictions",
                "across multiple jurisdictions",
                "laws in certain jurisdictions",
                "international tax laws",
            ],
        },
    },

    "Risk & Compliance": {
        "type": "filing",
        "sections": [
            "risk_factors",
            "business_overview",
            "management_discussion",
        ],
        "items": {
            "Cybersecurity risks": [
                "cybersecurity incidents",
                "threats to security",
                "unauthorized access",
            ],
            "Regulatory and legal risks": [
                "regulatory requirements",
                "regulatory changes",
                "legal requirements",
                "government regulations",
            ],
            "Competition and market risks": [
                "intense competition",
                "competitive pressures",
                "highly competitive",
            ],
            "Economic and geopolitical risks": [
                "economic uncertainty",
                "geopolitical tensions",
                "geopolitical risks",
            ],
            "Supplier and supply chain risks": [
                "supplier disruptions",
                "supply chain disruptions",
                "limited suppliers",
            ],
            "Business continuity risks": [
                "business continuity",
                "prolonged service outages",
                "catastrophic event",
            ],
            "Data privacy risks": [
                "data privacy",
                "personal data",
                "data protection",
            ],
        },
    },
}


MAX_EVIDENCE_EXCERPTS = 3
MAX_EXCERPT_LENGTH = 1200


# ============================================================
# 2. GENERAL TEXT AND EVIDENCE UTILITIES
# ============================================================

def normalize_text(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def get_evidence_blocks(sections, section_keys):
    """
    Collect filing passages while retaining their source section.

    Paragraphs are combined into manageable blocks so evidence
    can be located without storing an entire filing section.
    """
    blocks = []

    for section_key in section_keys:
        section = sections.get(section_key, {})

        if not isinstance(section, dict):
            continue

        if not section.get("available"):
            continue

        content = section.get("content") or ""

        if not isinstance(content, str):
            continue

        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in content.splitlines()
            if line.strip()
        ]

        current = ""

        for line in lines:
            if not current:
                current = line
            elif len(current) + len(line) < 1800:
                current += " " + line
            else:
                blocks.append({
                    "text": current,
                    "source_section": section.get(
                        "title", section_key
                    ),
                })
                current = line

            if len(current) >= 1800:
                blocks.append({
                    "text": current,
                    "source_section": section.get(
                        "title", section_key
                    ),
                })
                current = ""

        if current:
            blocks.append({
                "text": current,
                "source_section": section.get(
                    "title", section_key
                ),
            })

    return blocks


def find_filing_evidence(terms, evidence_blocks):
    """
    Find evidence for one information point.

    Evidence is deduplicated and excerpts are centered around
    the matching terms.
    """
    normalized_terms = [
        normalize_text(term)
        for term in terms
        if normalize_text(term)
    ]

    matched_blocks = []
    matched_terms = set()
    source_sections = set()
    seen = set()

    for block in evidence_blocks:
        original_text = block["text"]
        normalized_block = normalize_text(original_text)

        block_matches = [
            term for term in normalized_terms
            if term in normalized_block
        ]

        if not block_matches or normalized_block in seen:
            continue

        seen.add(normalized_block)
        matched_terms.update(block_matches)
        source_sections.add(block["source_section"])

        first_match = min(
            normalized_block.find(term)
            for term in block_matches
        )

        start = max(0, first_match - 350)
        end = min(
            len(original_text),
            start + MAX_EXCERPT_LENGTH,
        )

        excerpt = original_text[start:end].strip()

        matched_blocks.append({
            "source_section": block["source_section"],
            "excerpt": excerpt,
            "matched_terms": sorted(block_matches),
        })

    return {
        "evidence_count": len(matched_blocks),
        "matched_terms": sorted(matched_terms),
        "source_sections": sorted(source_sections),
        "evidence": matched_blocks[:MAX_EVIDENCE_EXCERPTS],
    }


def find_structured_source(evidence_text, evidence_blocks):
    """Identify the filing section containing a structured value."""
    if not evidence_text:
        return "10-K filing"

    target = normalize_text(evidence_text[:150])

    for block in evidence_blocks:
        if target and target in normalize_text(block["text"]):
            return block["source_section"]

    return "10-K filing"


# ============================================================
# 3. FINANCIAL INFORMATION EXTRACTION
# ============================================================

def get_financial_metric(financials, metric_names):
    if not isinstance(financials, dict):
        return None

    for metric_name in metric_names:
        metric = financials.get(metric_name)

        if metric is not None:
            return metric

    return None


def financial_metric_available(financials, metric_names):
    metric = get_financial_metric(financials, metric_names)

    if metric is None:
        return False

    if isinstance(metric, (int, float)):
        return True

    if not isinstance(metric, dict):
        return False

    if metric.get("available") is True:
        return True

    for key in (
        "latest",
        "latest_value",
        "value",
        "history",
        "quarterly_history",
        "annual_history",
    ):
        value = metric.get(key)

        if value is not None and value != [] and value != {}:
            return True

    return False


def build_financial_evidence(metric):
    if isinstance(metric, (int, float)):
        return [{
            "source_section": "SEC Company Facts",
            "details": {"value": metric},
        }]

    if not isinstance(metric, dict):
        return []

    fields = (
        "latest",
        "latest_value",
        "value",
        "period_start",
        "period_end",
        "filing_date",
        "form",
        "period_type",
        "xbrl_tag",
        "frame",
        "unit",
        "units",
        "history",
        "quarterly_history",
        "annual_history",
    )

    details = {
        field: metric[field]
        for field in fields
        if metric.get(field) is not None
    }

    if not details:
        return []

    return [{
        "source_section": "SEC Company Facts",
        "details": details,
    }]


def build_financial_category(category_name, rule, financials):
    items = []

    for item_name, metric_names in rule["items"].items():
        metric = get_financial_metric(financials, metric_names)
        available = financial_metric_available(
            financials, metric_names
        )

        evidence = (
            build_financial_evidence(metric)
            if available else []
        )

        details = evidence[0]["details"] if evidence else {}

        extracted_value = details.get(
            "value",
            details.get(
                "latest_value",
                details.get("latest"),
            ),
        )

        items.append({
            "name": item_name,
            "status": "available" if available else "not_found",
            "extraction_status": (
                "disclosed" if available else "not_found"
            ),
            "source": (
                "SEC Company Facts" if available else None
            ),
            "evidence_count": len(evidence),
            "matched_terms": metric_names if available else [],
            "extracted_value": extracted_value,
            "unit": details.get(
                "unit", details.get("units")
            ),
            "reporting_period": details.get("period_end"),
            "evidence": evidence,
        })

    return build_category_result(category_name, items)


# ============================================================
# 4. HUMAN RESOURCES EXTRACTION
# ============================================================

def extract_employee_count(text):
    """Extract an explicitly disclosed company-wide employee count."""
    if not text:
        return None

    patterns = [
        r"employed\s+(?:approximately\s+|about\s+|over\s+|more than\s+)?"
        r"([\d,]+)\s+people\s+on\s+a\s+full[- ]time\s+basis",

        r"employed\s+(?:approximately\s+|about\s+|over\s+|more than\s+)?"
        r"([\d,]+)\s+(?:full[- ]time\s+)?employees",

        r"([\d,]+)\s+(?:full[- ]time\s+)?employees\s+worldwide",

        r"workforce\s+of\s+(?:approximately\s+|about\s+)?([\d,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        value = int(match.group(1).replace(",", ""))

        if value <= 0:
            continue

        return {
            "value": value,
            "unit": "employees",
            "evidence_text": text[
                max(0, match.start() - 150):
                min(len(text), match.end() + 250)
            ].strip(),
        }

    return None


def extract_workforce_distribution(text):
    """Extract explicitly disclosed domestic and international counts."""
    if not text:
        return None

    patterns = [
        r"([\d,]+)\s+in\s+the\s+U\.?S\.?"
        r"\s+and\s+([\d,]+)\s+internationally",

        r"([\d,]+)\s+in\s+the\s+United States"
        r"\s+and\s+([\d,]+)\s+internationally",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        domestic = int(match.group(1).replace(",", ""))
        international = int(match.group(2).replace(",", ""))

        return {
            "value": {
                "united_states": domestic,
                "international": international,
                "total": domestic + international,
            },
            "unit": "employees",
            "evidence_text": text[
                max(0, match.start() - 150):
                min(len(text), match.end() + 250)
            ].strip(),
        }

    return None


def extract_workforce_by_function(text):
    """
    Extract employee counts by function where the filing
    explicitly reports a number followed by 'were in' and
    a recognised function.
    """
    if not text:
        return None

    function_patterns = {
        "operations": r"operations",
        "product_research_and_development":
            r"product research and development",
        "sales_and_marketing": r"sales and marketing",
        "general_and_administration":
            r"general and administration",
    }

    extracted = {}
    evidence_parts = []

    for field_name, function_pattern in function_patterns.items():
        pattern = (
            r"([\d,]+)\s+were\s+in\s+"
            + function_pattern
            + r"\b"
        )

        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        extracted[field_name] = int(
            match.group(1).replace(",", "")
        )

        evidence_parts.append(
            text[
                max(0, match.start() - 80):
                min(len(text), match.end() + 180)
            ].strip()
        )

    if not extracted:
        return None

    return {
        "value": extracted,
        "unit": "employees",
        "evidence_text": " ".join(evidence_parts),
    }


# ============================================================
# 5. BUSINESS STRUCTURE AND PRODUCT EXTRACTION
# ============================================================

def extract_business_segments(text):
    """
    Extract business segments from explicit descriptions such as:

    Our Intelligent Cloud segment consists of ...
    """
    if not text:
        return None

    pattern = (
        r"(?P<name>[A-Z][A-Za-z&]+"
        r"(?:\s+(?:[A-Z][A-Za-z&]+|and|of|the)){1,6})"
        r"\s+Our\s+(?P=name)\s+segment\s+consists\s+of\s+"
        r"(?P<description>[^.!?]{20,700}[.!?])"
    )

    matches = re.finditer(
        pattern,
        text,
        flags=re.IGNORECASE,
    )

    segments = []
    seen = set()

    for match in matches:
        name = re.sub(
            r"\s+", " ", match.group("name")
        ).strip()

        description = match.group("description").strip()

        key = name.lower()

        if key in seen:
            continue

        seen.add(key)

        segments.append({
            "name": name,
            "description": description,
        })

    if not segments:
        return None

    evidence_text = " ".join(
        f"{item['name']}: {item['description']}"
        for item in segments
    )

    return {
        "value": segments,
        "unit": None,
        "evidence_text": evidence_text,
    }






def extract_business_descriptions(text):
    """
    Extract product and service disclosures.

    Supports:
    1. Bullet lists following 'This segment primarily comprises:'
    2. Heading-based disclosures, such as Apple's Products and Services.
    """

    if not text:
        return None

    # First try the existing bullet-based extraction.
    normalized_text = (
        text.replace("\uf0b7", "•")
            .replace("▪", "•")
            .replace("◦", "•")
    )

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in normalized_text.splitlines()
    ]

    results = []
    seen = set()

    def save_description(description):
        description = " ".join(description).strip()
        description = re.sub(r"\s+", " ", description)

        if not description:
            return

        normalized = normalize_text(description)

        if normalized and normalized not in seen:
            seen.add(normalized)
            results.append(description)

    # Existing bullet-list format.
    for index, line in enumerate(lines):

        if not re.search(
            r"this segment primarily comprises\s*:",
            line,
            re.IGNORECASE
        ):
            continue

        position = index + 1
        current_description = []
        bullet_started = False

        while position < len(lines):
            current = lines[position].strip()
            position += 1

            if not current:
                continue

            bullet_match = re.match(r"^[•]\s*(.*)$", current)

            if bullet_match:
                if current_description:
                    save_description(current_description)

                bullet_started = True
                bullet_text = bullet_match.group(1).strip()
                current_description = [bullet_text] if bullet_text else []
                continue

            if not bullet_started:
                break

            if not current_description:
                current_description = [current]
                continue

            save_description(current_description)
            current_description = []
            break

        if current_description:
            save_description(current_description)

    # Heading-based format.
    # Only used when the existing bullet extractor finds nothing.
    if not results:

        headings = {
            "iphone",
            "mac",
            "ipad",
            "wearables, home and accessories",
            "advertising",
            "applecare",
            "cloud services",
            "digital content",
            "payment services",
        }

        group_headings = {"products", "services"}

        current_heading = None
        current_description = []
        inside_group = False

        def finish_heading():
            if current_heading and current_description:
                description = " ".join(current_description).strip()

                # Remove a repeated product name at the start.
                description = re.sub(
                    rf"^{re.escape(current_heading)}\s+",
                    "",
                    description,
                    flags=re.IGNORECASE,
                )

                description = re.sub(r"\s+", " ", description).strip()

                if len(description) >= 25:
                    save_description([f"{current_heading}: {description}"])

        for line in lines:

            current = line.strip()

            if not current:
                continue

            if current.lower() in group_headings:
                finish_heading()
                current_heading = None
                current_description = []
                inside_group = True
                continue

            if inside_group and current.lower() in headings:
                finish_heading()
                current_heading = current
                current_description = []
                continue

            # Stop product extraction when the next major section begins.
            if inside_group and current.lower() in {
                "segments",
                "markets and distribution",
                "competition",
                "supply of components and computing resources",
                "research and development",
                "intellectual property",
                "business seasonality and product introductions",
                "human capital",
                "available information",
            }:
                finish_heading()
                break

            if current_heading:
                if current in {"®", "™", "©"}:
                    continue

                if re.match(
                    r"^(Apple Inc\.|Apple Inc\s*\|)",
                    current,
                    re.IGNORECASE
                ):
                    continue

                current_description.append(current)

        finish_heading()

    if not results:
        return None

    structured_results = []

    for description in results:
        words = description.split()

        # Use the first few words as a readable product/service name.
        name = " ".join(words[:6]).rstrip(" ,;:")
        structured_results.append({
            "name": name,
            "points": [description],
        })

    return {
    "value": results,
    "unit": None,
    "evidence_text": " ".join(results),
    }


# ============================================================
# 6. ITEM-SPECIFIC STRUCTURED EXTRACTION
# ============================================================

def extract_structured_value(item_name, evidence_blocks):
    """
    Run only the extractor belonging to the requested
    information point.

    This prevents one successful extraction from incorrectly
    marking unrelated information points as disclosed.
    """
    combined_text = "\n".join(
        block["text"] for block in evidence_blocks
    )

    if item_name == "Total employee count":
        return extract_employee_count(combined_text)

    if item_name == "Domestic and international workforce":
        return extract_workforce_distribution(combined_text)

    if item_name == "Employee distribution by function":
        return extract_workforce_by_function(combined_text)

    if item_name in (
        "Reportable business segments",
        "Operating segments",
        "Business segment descriptions",
    ):
        return extract_business_segments(combined_text)

    if item_name == "Products and services":
        return extract_business_descriptions(combined_text)

    return None


# ============================================================
# 7. FILING CATEGORY BUILDER
# ============================================================

def build_filing_category(
    category_name,
    rule,
    sections,
    filing_available,
    filing_source,
):
    evidence_blocks = get_evidence_blocks(
        sections,
        rule["sections"],
    )

    items = []

    for item_name, terms in rule["items"].items():

        # Evidence is searched specifically for this item.
        result = find_filing_evidence(
            terms,
            evidence_blocks,
        )

                # Use the business overview for product/service extraction.
        # Avoid strategy statements from management discussion.
        structured_evidence_blocks = evidence_blocks

        if item_name == "Products and services":

            business_section = sections.get(
                "business_overview",
                {}
            )

            structured_value = extract_business_descriptions(
                business_section.get("content") or ""
            )

        else:

            structured_value = extract_structured_value(
                item_name,
                evidence_blocks,
            )

        has_structured_value = (
            structured_value is not None
            and structured_value.get("value") is not None
        )

        # Only successfully extracted information counts as available.
        # A keyword match without an extracted value is not sufficient.

        available = has_structured_value

        if has_structured_value:
            extraction_status = "disclosed"
        else:
            extraction_status = "not_found"

        evidence = list(result["evidence"])
        source_sections = set(result["source_sections"])

        # Add evidence specifically supporting the structured value.
        if has_structured_value:
            evidence_text = structured_value["evidence_text"]

            structured_source = find_structured_source(
                evidence_text,
                evidence_blocks,
            )

            source_sections.add(structured_source)

            structured_evidence = {
                "source_section": structured_source,
                "excerpt": evidence_text[:MAX_EXCERPT_LENGTH],
                "matched_terms": result["matched_terms"],
            }

            # Avoid inserting the same excerpt twice.
            existing_excerpts = {
                normalize_text(item.get("excerpt", ""))
                for item in evidence
            }

            if normalize_text(
                structured_evidence["excerpt"]
            ) not in existing_excerpts:
                evidence.insert(0, structured_evidence)

        items.append({
            "name": item_name,
            "status": (
                "available" if available else "not_found"
            ),
            "extraction_status": extraction_status,
            "source": (
                sorted(source_sections) if available else None
            ),
            "evidence_count": (
                result["evidence_count"]
                + (1 if has_structured_value else 0)
            ),
            "matched_terms": result["matched_terms"],
            "extracted_value": (
                structured_value["value"]
                if has_structured_value else None
            ),
            "unit": (
                structured_value.get("unit")
                if has_structured_value else None
            ),
            "reporting_period": filing_source.get(
                "reporting_period"
            ),
            "evidence": evidence[:MAX_EVIDENCE_EXCERPTS],
        })

    category_result = build_category_result(
        category_name,
        items,
    )

    if not filing_available:
        category_result["status"] = "not_found"

    return category_result


# ============================================================
# 8. CATEGORY SUMMARY
# ============================================================

def build_category_result(category_name, items):
    available_count = sum(
        1
        for item in items
        if item["status"] == "available"
    )

    if available_count == 0:
        status = "not_found"
    elif available_count == len(items):
        status = "available"
    else:
        status = "partially_available"

    return {
        "department": category_name,
        "status": status,
        "available_items": available_count,
        "total_items_checked": len(items),
        "data_items": items,
    }


# ============================================================
# 9. MAIN COMPANY INTELLIGENCE BUILDER
# ============================================================

def extract_company_intelligence(
    business_information,
    financials=None,
):
    """
    Build an evidence-backed company information inventory.

    Preserves the existing categories, data item names and
    overall response structure.
    """
    if not isinstance(business_information, dict):
        business_information = {}

    if not isinstance(financials, dict):
        financials = {}

    sections = business_information.get("sections", {})

    if not isinstance(sections, dict):
        sections = {}

    filing_available = bool(
        business_information.get("available")
    )

    filing_source = {
        "form": business_information.get("form"),
        "filing_date": business_information.get("filing_date"),
        "reporting_period": business_information.get("report_date"),
        "url": business_information.get("document_url"),
    }

    categories = []

    for category_name, rule in DATA_CATALOG.items():
        start_time = time.perf_counter()

        print(
            f"[INTELLIGENCE] Starting: {category_name}",
            flush=True
        )

        if rule["type"] == "financial":
            category = build_financial_category(
                category_name,
                rule,
                financials,
            )
        else:
            category = build_filing_category(
                category_name,
                rule,
                sections,
                filing_available,
                filing_source,
            )

        categories.append(category)

        elapsed = time.perf_counter() - start_time

        print(
            f"[INTELLIGENCE] Completed: {category_name} "
            f"in {elapsed:.2f}s",
            flush=True
        )

    total_items = sum(
        category["total_items_checked"]
        for category in categories
    )

    available_items = sum(
        category["available_items"]
        for category in categories
    )

    disclosed_items = sum(
        1
        for category in categories
        for item in category["data_items"]
        if item.get("extraction_status") == "disclosed"
    )

    mentioned_items = sum(
        1
        for category in categories
        for item in category["data_items"]
        if item.get("extraction_status") == "mentioned"
    )

    return {
        "available": available_items > 0,
        "title": "Company Data Availability",
        "description": (
            "Evidence-backed organizational, financial, "
            "operational, and business information identified "
            "in SEC filings."
        ),
        "filing": filing_source,
        "summary": {
            "total_categories": len(categories),
            "total_data_items_checked": total_items,
            "available_data_items": available_items,
            "not_found_data_items": (
                total_items - available_items
            ),
            "directly_extracted_items": disclosed_items,
            "mentioned_items": mentioned_items,
        },
        "categories": categories,
        "extraction_method": (
            "rule_based_evidence_and_value_extraction"
        ),
        "limitations": [
            (
                "A mentioned item means matching disclosure text "
                "was found; it does not mean a specific value or "
                "system was extracted."
            ),
            (
                "A directly extracted value is returned only when "
                "an explicit extraction rule identifies it in "
                "the source."
            ),
            (
                "Not found means no matching information was "
                "identified in the retrieved sources. It does "
                "not prove the company does not have that information."
            ),
            (
                "SEC filings may disclose company-wide employee "
                "counts without disclosing department-level "
                "workforce numbers."
            ),
            (
                "A complete internal software and technology "
                "inventory is generally not available from SEC "
                "filings alone."
            ),
            (
                "Financial account availability depends on the "
                "XBRL facts retrieved by the financial extractor."
            ),
        ],
    }
