
import html
import re
from bs4 import BeautifulSoup


# SEC filing section identifiers
SECTION_ITEMS = {
    "business_overview": ("I", "1"),
    "risk_factors": ("I", "1A"),
    "management_discussion": ("II", "7"),
}

SECTION_LABELS = {
    "business_overview": "Item 1 — Business",
    "risk_factors": "Item 1A — Risk Factors",
    "management_discussion": (
        "Item 7 — Management's Discussion and Analysis"
    ),
    "workforce_information": "Workforce-related disclosures",
}

PART_PATTERN = re.compile(
    r"^\s*PART\s+(IV|III|II|I)\s*$",
    re.IGNORECASE
)

ITEM_PATTERN = re.compile(
    r"^\s*ITEM\s+"
    r"(1A|1B|1C|1|2|3|4|5|6|7A|7|8|9A|9B|9C|9|"
    r"10|11|12|13|14|15|16)"
    r"\s*\.?\s*.*$",
    re.IGNORECASE
)

WORKFORCE_KEYWORDS = [
    "human capital",
    "number of employees",
    "employees worldwide",
    "full-time employees",
    "our employees",
    "workforce",
    "employee engagement",
    "talent development",
    "employee development",
    "talent management",
    "employee retention",
    "employee compensation",
    "employee benefits",
]


def clean_document(html):
    """
    Convert SEC HTML into readable lines.

    Accepts bytes or text. Passing bytes allows BeautifulSoup
    to detect the original document encoding.
    """
    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "ix:header",
        "ix:hidden"
    ]):
        element.decompose()

    lines = []

    for line in soup.get_text(separator="\n").splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return lines


def get_previous_non_page_line(lines, index):
    """
    Find the preceding meaningful line, ignoring page numbers.
    """
    for position in range(index - 1, max(-1, index - 5), -1):
        value = lines[position].strip()

        if value.isdigit():
            continue

        return value

    return ""


def identify_item_markers(lines):
    """
    Identify SEC item markers using the current Part context.

    A Part heading applies to subsequent Item headings until
    another Part heading is encountered.
    """
    markers = []
    current_part = None

    for index, line in enumerate(lines):
        part_match = PART_PATTERN.match(line)

        if part_match:
            current_part = part_match.group(1).upper()
            continue

        item_match = ITEM_PATTERN.match(line)

        if not item_match or current_part is None:
            continue

        markers.append({
            "index": index,
            "part": current_part,
            "item": item_match.group(1).upper(),
        })

    return markers

def find_item_section(lines, target_part, target_item):
    markers = identify_item_markers(lines)
    candidates = []

    for marker in markers:
        if marker["part"] != target_part or marker["item"] != target_item:
            continue

        start_index = marker["index"] + 1

        # Skip page numbers and empty lines when examining
        # the first meaningful line after the Item marker.
        first_content_index = start_index

        while first_content_index < len(lines):
            value = lines[first_content_index].strip()

            if not value or value.isdigit():
                first_content_index += 1
                continue

            break

        if first_content_index >= len(lines):
            continue

        first_content = lines[first_content_index].strip().lower()

        # Reject the Business table-of-contents entry.
        if (
            target_part == "I"
            and target_item == "1"
            and first_content == "business"
        ):
            continue

        # Reject the forward-looking statements reference.
        if (
            target_part == "I"
            and target_item == "1"
            and "forward-looking statements" in first_content
        ):
            continue

        end_index = len(lines)

        # Find the next different Item in the same Part.
        # Repeated page headers for the current Item are ignored.
        for next_marker in markers:
            if next_marker["index"] <= marker["index"]:
                continue

            if next_marker["part"] != target_part:
                continue

            if next_marker["item"] != target_item:
                end_index = next_marker["index"]
                break

        content_lines = []

        for index in range(start_index, end_index):
            line = lines[index].strip()

            if not line or line.isdigit():
                continue

            if PART_PATTERN.match(line):
                continue

            if ITEM_PATTERN.match(line):
                continue

            content_lines.append(line)

        content = "\n".join(content_lines).strip()

        if len(content) < 1000:
            continue

        candidates.append({
            "start_index": marker["index"],
            "content": content
        })

    if not candidates:
        return None

    # Choose the longest valid candidate after filtering TOC
    # and forward-looking statements entries.
    best_candidate = max(
        candidates,
        key=lambda candidate: len(candidate["content"])
    )

    return best_candidate["content"]

def extract_workforce_information(text):
    """
    Find workforce-related disclosures in extracted filing text.
    """
    if not text:
        return None

    lines = text.splitlines()
    matched_sections = []
    seen = set()

    for index, line in enumerate(lines):
        lower_line = line.lower()

        if not any(
            keyword in lower_line
            for keyword in WORKFORCE_KEYWORDS
        ):
            continue

        start = max(0, index - 2)
        end = min(len(lines), index + 4)

        excerpt = "\n".join(lines[start:end]).strip()

        if excerpt and excerpt not in seen:
            seen.add(excerpt)
            matched_sections.append(excerpt)

    if not matched_sections:
        return None

    return "\n\n---\n\n".join(matched_sections[:15])


def extract_10k_sections(html):
    """
    Extract major sections from an SEC 10-K filing.
    """
    lines = clean_document(html)

    extracted = {}

    for key, (part, item) in SECTION_ITEMS.items():
        extracted[key] = find_item_section(
            lines,
            target_part=part,
            target_item=item
        )

    # Workforce disclosures may appear in both Business and MD&A.
    workforce_source = "\n\n".join(
        content
        for content in [
            extracted.get("business_overview"),
            extracted.get("management_discussion"),
        ]
        if content
    )

    extracted["workforce_information"] = (
        extract_workforce_information(workforce_source)
    )

    sections = {}

    for key, content in extracted.items():
        sections[key] = {
            "title": SECTION_LABELS[key],
            "available": bool(content),
            "content": content,
        }

    return sections
