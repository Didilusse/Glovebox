import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

from pypdf import PdfReader


MAX_PDF_PAGES = 25
MAX_EXTRACTED_TEXT = 1_000_000
DATE_RE = re.compile(r"^\s*(\d{2}/\d{2}/\d{4})(?:\s+(.*))?$")
VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b", re.IGNORECASE)

OCR_CORRECTIONS = {
    "dlter": "filter",
    "elter": "filter",
    "flter": "filter",
    "?lter": "filter",
    "huid": "fluid",
    "juid": "fluid",
    "hushed": "flushed",
    "jushed": "flushed",
    "redlls": "refills",
    "Verided": "Verified",
}


class CarfaxParseError(ValueError):
    pass


@dataclass
class ParsedServiceRecord:
    date_of_service: date
    mileage: int | None
    service_provider: str | None
    work_items: list[str]
    page: int
    category: str = "other"
    warnings: list[str] = field(default_factory=list)

    @property
    def work_done(self) -> str:
        return "; ".join(self.work_items)


@dataclass
class ParsedCarfaxReport:
    vin: str
    vehicle: str | None
    year: int | None
    make: str | None
    model: str | None
    fuel_type: str | None
    records: list[ParsedServiceRecord]
    warnings: list[str] = field(default_factory=list)


def extract_pdf_pages(pdf_bytes: bytes) -> list[str]:
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise CarfaxParseError("The uploaded file is not a readable PDF") from exc

    if reader.is_encrypted:
        raise CarfaxParseError("Encrypted PDFs are not supported")
    if not reader.pages:
        raise CarfaxParseError("The PDF has no pages")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise CarfaxParseError(f"The PDF exceeds the {MAX_PDF_PAGES}-page limit")

    pages: list[str] = []
    total_length = 0
    for page in reader.pages:
        try:
            text = page.extract_text(extraction_mode="layout") or ""
        except TypeError:
            text = page.extract_text() or ""
        total_length += len(text)
        if total_length > MAX_EXTRACTED_TEXT:
            raise CarfaxParseError("The PDF contains too much extracted text")
        pages.append(text)

    if sum(bool(page.strip()) for page in pages) == 0:
        raise CarfaxParseError("No text could be extracted; scanned reports are not supported")
    return pages


def parse_carfax_pages(pages: list[str]) -> ParsedCarfaxReport:
    full_text = "\n".join(pages)
    if "CARFAX Vehicle History Report" not in full_text:
        raise CarfaxParseError("This does not appear to be a CARFAX Vehicle History Report")

    vin_match = VIN_RE.search(full_text)
    if not vin_match:
        raise CarfaxParseError("The CARFAX VIN could not be found")
    vin = vin_match.group(1).upper()

    vehicle_match = re.search(
        r"for this\s+(\d{4})\s+(.+?):\s*[A-HJ-NPR-Z0-9]{17}",
        full_text,
        re.IGNORECASE,
    )
    year = int(vehicle_match.group(1)) if vehicle_match else None
    description = vehicle_match.group(2).strip() if vehicle_match else None
    vehicle = f"{year} {description}" if year and description else None
    make, model = _split_vehicle_description(description)
    fuel_type = None
    if re.search(r"\bGasoline\b", full_text, re.IGNORECASE):
        fuel_type = "gas"
    elif re.search(r"\bDiesel\b", full_text, re.IGNORECASE):
        fuel_type = "diesel"
    elif re.search(r"\bElectric\b", full_text, re.IGNORECASE):
        fuel_type = "electric"

    detailed_seen = False
    record_blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    current_page = 0

    for page_number, page_text in enumerate(pages, start=1):
        for original_line in page_text.splitlines():
            line = original_line.strip()
            if not detailed_seen:
                if "Detailed History" in line:
                    detailed_seen = True
                continue
            if "Glossary" in line:
                if current:
                    record_blocks.append((current_page, current))
                current = None
                detailed_seen = False
                break
            if DATE_RE.match(line):
                if current:
                    record_blocks.append((current_page, current))
                current = [line]
                current_page = page_number
            elif current is not None:
                current.append(line)

    if current:
        record_blocks.append((current_page, current))
    if not record_blocks:
        raise CarfaxParseError("No Detailed History records were found")

    records: list[ParsedServiceRecord] = []
    last_seen_mileage: int | None = None
    for page_number, lines in record_blocks:
        first_match = DATE_RE.match(lines[0])
        if not first_match:
            continue
        record_date = _parse_date(first_match.group(1))
        remainder = first_match.group(2) or ""
        body_lines = ([remainder] if remainder else []) + lines[1:]
        mileage, body_lines = _take_mileage(body_lines)
        mileage_warning = None
        if mileage is not None:
            if last_seen_mileage is not None and mileage < last_seen_mileage:
                mileage_warning = (
                    f"Mileage {mileage:,} is lower than the prior report reading "
                    f"of {last_seen_mileage:,}"
                )
            last_seen_mileage = mileage

        marker_index = next(
            (index for index, line in enumerate(body_lines) if "Vehicle serviced" in line),
            None,
        )
        if marker_index is None:
            continue

        marker_line = body_lines[marker_index]
        before_marker, _, marker_remainder = marker_line.partition("Vehicle serviced")
        provider_lines = body_lines[:marker_index] + ([before_marker] if before_marker.strip() else [])
        provider = _extract_provider(provider_lines)
        comment_lines = ([marker_remainder] if marker_remainder.strip() else []) + body_lines[marker_index + 1:]
        work_items = _extract_work_items(comment_lines)
        if not work_items:
            work_items = ["Vehicle serviced"]

        warnings: list[str] = []
        if mileage is None:
            warnings.append("Mileage was not reported by CARFAX")
        if mileage_warning:
            warnings.append(mileage_warning)
        record = ParsedServiceRecord(
            date_of_service=record_date,
            mileage=mileage,
            service_provider=provider,
            work_items=work_items,
            page=page_number,
            warnings=warnings,
        )
        record.category = classify_category(work_items)
        records.append(record)

    if not records:
        raise CarfaxParseError("No Vehicle serviced records were found")
    return ParsedCarfaxReport(
        vin=vin,
        vehicle=vehicle,
        year=year,
        make=make,
        model=model,
        fuel_type=fuel_type,
        records=records,
    )


def make_source_record_key(
    vin: str,
    service_date: date,
    mileage: int | None,
    provider: str | None,
    work_done: str,
) -> str:
    normalized = "|".join(
        [
            vin.upper(),
            service_date.isoformat(),
            str(mileage) if mileage is not None else "",
            _normalize_for_key(provider or ""),
            _normalize_for_key(work_done),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def classify_category(items: list[str]) -> str:
    groups: set[str] = set()
    for item in items:
        value = item.lower()
        if any(word in value for word in ("brake", "caliper", "rotor")):
            groups.add("brakes")
        elif any(word in value for word in ("tire", "wheel", "alignment")):
            groups.add("wheels")
        elif any(word in value for word in ("oil", "fluid", "coolant", "antifreeze")):
            groups.add("fluids")
        elif any(word in value for word in ("wiper", "light bulb", "floor mat")):
            groups.add("exterior")
        elif any(word in value for word in ("belt", "pump", "alternator", "battery", "filter")):
            groups.add("engine")
        elif any(word in value for word in ("suspension", "driveshaft", "steering")):
            groups.add("suspension")
    return next(iter(groups)) if len(groups) == 1 else "other"


def _parse_date(value: str) -> date:
    month, day, year = (int(part) for part in value.split("/"))
    return date(year, month, day)


def _take_mileage(lines: list[str]) -> tuple[int | None, list[str]]:
    remaining = list(lines)
    while remaining and not remaining[0].strip():
        remaining.pop(0)
    if not remaining:
        return None, remaining
    match = re.match(r"^\s*(\d{1,3}(?:,\d{3})+|\d{1,6})(?:\s+(.*))?$", remaining[0])
    if not match:
        return None, remaining
    mileage = int(match.group(1).replace(",", ""))
    tail = match.group(2)
    remaining = ([tail] if tail else []) + remaining[1:]
    return mileage, remaining


def _extract_provider(lines: list[str]) -> str | None:
    for line in lines:
        candidates = re.split(r"\s{2,}", line.strip())
        for candidate in candidates:
            candidate = candidate.strip(" -")
            if not candidate or _is_noise(candidate):
                continue
            return _correct_ocr(candidate)
    return None


def _extract_work_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        parts = re.split(r"\s+-\s*", line)
        # Layout extraction can preserve the source and comments columns on one line.
        if len(parts) > 1 and not line.lstrip().startswith("-"):
            parts = parts[1:]
        for candidate in parts:
            candidate = _correct_ocr(candidate.strip(" -"))
            if not candidate or _is_noise(candidate):
                continue
            if candidate in {"Vehicle serviced", "Comments"}:
                continue
            items.append(candidate)
    return list(dict.fromkeys(items))


def _correct_ocr(value: str) -> str:
    for wrong, right in OCR_CORRECTIONS.items():
        value = re.sub(rf"(?<!\w){re.escape(wrong)}(?!\w)", right, value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def _is_noise(value: str) -> bool:
    lower = value.lower()
    return (
        lower.startswith("carfax vehicle history report")
        or lower.startswith("http")
        or re.fullmatch(r"page \d+ of \d+", lower) is not None
        or re.fullmatch(r"\d{3}-\d{3}-\d{4}", value) is not None
        or re.fullmatch(r"[A-Za-z .'-]+,\s*[A-Z]{2}", value) is not None
        or "verified reviews" in lower
        or "customer favorite" in lower
        or lower.endswith(".com/")
        or lower.endswith(".com")
        or lower.startswith("owner ")
        or lower.startswith("purchased:")
        or lower in {"personal vehicle", "lease vehicle"}
        or re.fullmatch(r"\d[\d,]* mi/yr", lower) is not None
        or lower in {"date mileage source comments", "date", "mileage", "source", "comments"}
        or "manufacturer recommended maintenance schedules" in lower
        or "have questions?" in lower
    )


def _normalize_for_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _split_vehicle_description(description: str | None) -> tuple[str | None, str | None]:
    if not description:
        return None, None
    multi_word_makes = (
        "ALFA ROMEO",
        "ASTON MARTIN",
        "LAND ROVER",
        "MERCEDES BENZ",
        "MERCEDES-BENZ",
        "ROLLS ROYCE",
        "ROLLS-ROYCE",
    )
    upper = description.upper()
    for make in multi_word_makes:
        if upper.startswith(f"{make} "):
            return _format_make(description[:len(make)]), description[len(make):].strip()
    make, separator, model = description.partition(" ")
    return (_format_make(make), model.strip()) if separator else (_format_make(make), None)


def _format_make(make: str) -> str:
    upper = make.upper()
    acronyms = {"BMW", "BYD", "FIAT", "GMC", "MINI"}
    return upper if upper in acronyms else make.title()
