"""
Parse rate-chart tables from PDF, Excel, and CSV.
Returns list of dicts: age_band_key, plan_key, gender, rate (string).
Caller maps keys to Plan/AgeBand and inserts ProductPrice.
"""
import csv
import io
import re
from decimal import Decimal, InvalidOperation

# Optional: pdfplumber and openpyxl
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import openpyxl
except ImportError:
    openpyxl = None


# Normalize plan header text to our Plan.code (e.g. "Silver Premium" -> SILVER_PREMIUM)
PLAN_ALIASES = {
    "gold": "GOLD",
    "silver premium": "SILVER_PREMIUM",
    "silver classic": "SILVER_CLASSIC",
    "green": "GREEN",
    "emerald": "EMERALD",
    "pearl": "PEARL",
    "silk road": "SILK_ROAD",
    "silkroad": "SILK_ROAD",
}

# Normalize age band label/code to our AgeBand.code
AGE_BAND_ALIASES = {
    "0-1": "000-001",
    "0 - 1": "000-001",
    "000-001": "000-001",
    "2-5": "002-005",
    "2 - 5": "002-005",
    "002-005": "002-005",
    "6-15": "006-015",
    "006-015": "006-015",
    "16-20": "016-020",
    "016-020": "016-020",
    "21-25": "021-025",
    "021-025": "021-025",
    "26-30": "026-030",
    "026-030": "026-030",
    "31-35": "031-035",
    "031-035": "031-035",
    "36-40": "036-040",
    "036-040": "036-040",
    "41-45": "041-045",
    "041-045": "041-045",
    "46-50": "046-050",
    "046-050": "046-050",
    "51-55": "051-055",
    "051-055": "051-055",
    "56-59": "056-059",
    "056-059": "056-059",
    "60": "060",
    "061-065": "061-065",
    "66-70": "066-070",
    "066-070": "066-070",
    "71-75": "071-075",
    "071-075": "071-075",
    "76-99": "076-099",
    "076-099": "076-099",
}


def _normalize_plan_header(cell):
    """Return plan code only (no gender). Used when we don't need gender from header."""
    plan_key, _ = _parse_plan_header_and_gender(cell)
    return plan_key


def _parse_plan_header_and_gender(cell):
    """Parse column header to (plan_key, gender). Gender: M, F, or B.
    Detects e.g. 'GOLD MALE', 'GOLD M', 'Silver Premium Female', 'MALE', 'FEMALE'.
    """
    if cell is None:
        return None, "B"
    raw = str(cell).strip()
    s = re.sub(r"\s+", " ", raw).strip().lower()
    gender = "B"
    # Suffix patterns for Male/Female (so "GOLD M" or "GOLD MALE" -> plan GOLD, gender M)
    if re.search(r"\s*male\s*$", s) or re.search(r"\s+m\s*$", s):
        gender = "M"
        s = re.sub(r"\s*male\s*$", "", s, flags=re.I).strip()
        s = re.sub(r"\s+m\s*$", "", s, flags=re.I).strip()
    elif re.search(r"\s*female\s*$", s) or re.search(r"\s+f\s*$", s):
        gender = "F"
        s = re.sub(r"\s*female\s*$", "", s, flags=re.I).strip()
        s = re.sub(r"\s+f\s*$", "", s, flags=re.I).strip()
    plan_key = PLAN_ALIASES.get(s) or (s.replace(" ", "_").upper() if s else None)
    return plan_key, gender


def _normalize_age_band(cell):
    if cell is None:
        return None
    s = str(cell).strip()
    # Remove brackets like [000-001]
    s = re.sub(r"^\[|\]$", "", s).strip()
    s_lower = s.lower().replace(" ", "")
    for k, v in AGE_BAND_ALIASES.items():
        if k.replace(" ", "").lower() == s_lower or k == s:
            return v
    if s.isdigit() and len(s) <= 2:
        age = int(s)
        if age <= 1:
            return "000-001"
        if age <= 5:
            return "002-005"
        if age <= 15:
            return "006-015"
        if age <= 20:
            return "016-020"
        if age <= 25:
            return "021-025"
        if age <= 30:
            return "026-030"
        if age <= 35:
            return "031-035"
        if age <= 40:
            return "036-040"
        if age <= 45:
            return "041-045"
        if age <= 50:
            return "046-050"
        if age <= 55:
            return "051-055"
        if age <= 59:
            return "056-059"
        if age == 60:
            return "060"
        if age <= 65:
            return "061-065"
        if age <= 70:
            return "066-070"
        if age <= 75:
            return "071-075"
        if age <= 99:
            return "076-099"
    return None


def _parse_number(val):
    if val is None or val == "":
        return None
    s = str(val).strip().replace(",", "")
    try:
        return str(Decimal(s))
    except (InvalidOperation, ValueError):
        return None


def _column_headers_with_two_rows(rows, row0_idx, row1_idx):
    """Build (plan_key, gender) per column when table has two header rows: row0 = plans, row1 = MALE/FEMALE.
    Fills forward so repeated plan names (e.g. GOLD, GOLD) get correct plan from first occurrence.
    Column 0 is typically Age Band / Network and is skipped for plan resolution.
    """
    ncols = max(len(rows[row0_idx]) if row0_idx < len(rows) else 0, len(rows[row1_idx]) if row1_idx < len(rows) else 0)
    if ncols < 2:
        return None
    result = []
    last_plan_key = None
    for c in range(ncols):
        r0 = (rows[row0_idx][c] if c < len(rows[row0_idx]) else None) or ""
        r1 = (rows[row1_idx][c] if c < len(rows[row1_idx]) else None) or ""
        r0, r1 = str(r0).strip().lower(), str(r1).strip().lower()
        # Parse plan from first row (e.g. "gold", "silver premium"); empty = use previous column's plan
        plan_key, _ = _parse_plan_header_and_gender(r0) if r0 else (None, "B")
        if plan_key:
            last_plan_key = plan_key
        if not plan_key and last_plan_key:
            plan_key = last_plan_key
        # Second row: MALE / FEMALE
        gender = "B"
        if r1 in ("male", "m"):
            gender = "M"
        elif r1 in ("female", "f"):
            gender = "F"
        result.append((plan_key, gender))
    return result if any(t[0] for t in result) else None


def _table_to_rates(table, header_row_idx=0):
    """Convert 2D table (list of lists) to list of {age_band_key, plan_key, gender, rate}."""
    if not table or len(table) <= header_row_idx + 1:
        return []
    rows = table
    age_col_idx = 0
    rates = []
    # Try two-row header first (e.g. row0 = GOLD, GOLD, SILVER... row1 = MALE, FEMALE, MALE, FEMALE)
    column_headers = None
    data_start = header_row_idx + 1
    if header_row_idx + 2 <= len(rows):
        two_row = _column_headers_with_two_rows(rows, header_row_idx, header_row_idx + 1)
        if two_row and any(t[0] for t in two_row) and any(t[1] in ("M", "F") for t in two_row):
            column_headers = two_row
            data_start = header_row_idx + 2
    if column_headers is None:
        # Single-row header (e.g. "GOLD MALE", "GOLD FEMALE")
        headers = [str(h).strip() if h is not None else "" for h in rows[header_row_idx]]
        column_headers = [_parse_plan_header_and_gender(headers[c] if c < len(headers) else "") for c in range(max(len(headers), 2))]
    for r_idx in range(data_start, len(rows)):
        row = rows[r_idx]
        if not row:
            continue
        age_cell = row[age_col_idx] if age_col_idx < len(row) else None
        age_key = _normalize_age_band(age_cell)
        if not age_key:
            continue
        for col_idx in range(1, min(len(row), len(column_headers))):
            if col_idx >= len(column_headers):
                break
            plan_key, gender = column_headers[col_idx] if col_idx < len(column_headers) else (None, "B")
            if not plan_key:
                continue
            rate_val = _parse_number(row[col_idx] if col_idx < len(row) else None)
            if rate_val is not None:
                rates.append({"age_band_key": age_key, "plan_key": plan_key, "gender": gender, "rate": rate_val})
    return rates


def _find_best_table_pdf(tables):
    """Pick the largest table that looks like a rate matrix (many rows, many cols, numbers)."""
    best = []
    for t in tables:
        if not t or len(t) < 2:
            continue
        rows = len(t)
        cols = max(len(r) for r in t) if t else 0
        if cols < 2:
            continue
        # Prefer tables with more rows and columns
        if rows * cols > len(best) * (max(len(r) for r in best) if best else 0):
            best = t
    return best


def parse_pdf(file_content: bytes) -> list:
    """Extract rate table from PDF. file_content is raw bytes."""
    if not pdfplumber:
        raise ValueError("pdfplumber is not installed")
    rates = []
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue
            best = _find_best_table_pdf(tables)
            if best:
                page_rates = _table_to_rates(best, 0)
                if not page_rates and len(best) > 2:
                    page_rates = _table_to_rates(best, 1)
                rates.extend(page_rates)
    return rates


def parse_excel(file_content: bytes, filename: str = "") -> list:
    """Extract rate table from Excel (.xlsx). Uses first sheet."""
    if not openpyxl:
        raise ValueError("openpyxl is not installed")
    wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
    sheet = wb.active
    if not sheet:
        return []
    rows = []
    for row in sheet.iter_rows(values_only=True):
        rows.append([v for v in row])
    wb.close()
    if not rows:
        return []
    return _table_to_rates(rows, 0)


def parse_csv(file_content: bytes, filename: str = "") -> list:
    """Extract rate table from CSV. Tries utf-8 then latin-1."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            text = file_content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = file_content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return []
    return _table_to_rates(rows, 0)


def parse_upload(file_content: bytes, filename: str) -> list:
    """Dispatch by extension. Returns list of {age_band_key, plan_key, gender, rate}."""
    fn = (filename or "").lower()
    if fn.endswith(".pdf"):
        return parse_pdf(file_content)
    if fn.endswith(".xlsx") or fn.endswith(".xls"):
        return parse_excel(file_content, filename)
    if fn.endswith(".csv"):
        return parse_csv(file_content, filename)
    raise ValueError("Unsupported file type. Use .pdf, .xlsx, .xls, or .csv")
