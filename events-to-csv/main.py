import re
import csv
from datetime import datetime

INPUT_FILE = "events.txt"
OUTPUT_FILE = "events.csv"

# =========================================================
# KONFIGURATION
# =========================================================

DEFAULT_LOCATION = "Klublokal"

CATEGORY_KLUBABEND = ""
CATEGORY_FERIEN = ""
CATEGORY_SGM = "SGM/SMM"
CATEGORY_SMM = "SGM/SMM"
CATEGORY_KLUBMEISTERSCHAFT = "Klubmeisterschaft"
CATEGORY_STADTMEISTERSCHAFT = "Stadtmeisterschaft"

# =========================================================

MONTHS = {
    "jan": 1,
    "feb": 2,
    "märz": 3,
    "maerz": 3,
    "apr": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "aug": 8,
    "sept": 9,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dez": 12,
}


def normalize_month(text):
    return text.lower().replace(".", "").strip()


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def format_date(year, month, day):
    return datetime(year, month, day).strftime("%Y-%m-%d")


def detect_category(title):
    lower = title.lower()

    if "sgm" in lower:
        return CATEGORY_SGM

    if "smm" in lower:
        return CATEGORY_SMM

    if "klubmeisterschaft" in lower:
        return CATEGORY_KLUBMEISTERSCHAFT

    if "stadtmeisterschaft" in lower or re.search(r"\bstm\b", lower):
        return CATEGORY_STADTMEISTERSCHAFT

    return ""


def needs_location(title):
    lower = title.lower()

    if "sgm" in lower or "smm" in lower:
        return False

    return True


def normalize_title(title):

    # StM ausschreiben
    title = re.sub(
        r"\bStM\b",
        "Stadtmeisterschaft",
        title,
        flags=re.IGNORECASE,
    )

    # "3. R." -> "3. Runde"
    title = re.sub(
        r"(\d+)\.\s*R\.",
        r"\1. Runde",
        title,
        flags=re.IGNORECASE,
    )

    # doppelte Leerzeichen entfernen
    title = clean_text(title)

    return title


def create_event(
    title,
    start_date,
    end_date=None,
    start_time="",
    category="",
):
    if end_date is None:
        end_date = start_date

    location = DEFAULT_LOCATION if needs_location(title) else ""

    return {
        "title": normalize_title(title),
        "startdate": start_date,
        "enddate": end_date,
        "starttime": start_time,
        "location": location,
        "content": "",
        "category_slugs": category,
    }


def split_combined_events(title):
    """
    Zerlegt kombinierte Zeilen wie:
    'Klubmeisterschaft 2. R. Stadtmeisterschaft 1. + 2. R.'
    """

    title = normalize_title(title)

    parts = []

    km_match = re.search(
        r"(Klubmeisterschaft.*?(?=(Stadtmeisterschaft|$)))",
        title,
        flags=re.IGNORECASE,
    )

    stm_match = re.search(
        r"(Stadtmeisterschaft.*$)",
        title,
        flags=re.IGNORECASE,
    )

    if km_match:
        parts.append(clean_text(km_match.group(1)))

    if stm_match:
        parts.append(clean_text(stm_match.group(1)))

    if parts:
        return parts

    return [title]


def parse_holiday(line, current_year):
    """
    Beispiele:
    Sportferien (25.1. – 1.2.)
    Weihnachtsferien (20.12.26 – 3.1.27)
    Frühlingsferien (Fr 3.4. – 19.4.)
    """

    match = re.match(
        r"^(.*?)\s*\((?:[A-Za-z]{2}\s*)?(\d{1,2})\.(\d{1,2})(\d{2})?\.\s*[–-]\s*(?:[A-Za-z]{2}\s*)?(\d{1,2})\.(\d{1,2})(\d{2})?\.\)",
        line
    )

    if not match:
        return None

    title = clean_text(match.group(1))

    start_day = int(match.group(2))
    start_month = int(match.group(3))
    start_year = match.group(4)

    end_day = int(match.group(5))
    end_month = int(match.group(6))
    end_year = match.group(7)

    if start_year:
        start_year = 2000 + int(start_year)
    else:
        start_year = current_year

    if end_year:
        end_year = 2000 + int(end_year)
    else:
        end_year = start_year

        if end_month < start_month:
            end_year += 1

    start_date = format_date(start_year, start_month, start_day)
    end_date = format_date(end_year, end_month, end_day)

    return create_event(
        title=title,
        start_date=start_date,
        end_date=end_date,
        category=CATEGORY_FERIEN,
    )


def parse_file(path):
    events = []

    current_month = None
    current_year = None

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:

        # =====================================================
        # FERIEN
        # =====================================================

        holiday = parse_holiday(line, current_year)

        if holiday:
            events.append(holiday)
            continue

        # =====================================================
        # NORMALE TERMINE
        # =====================================================

        match = re.match(
            r"^(Mo|Di|Mi|Do|Fr|Sa|So)\s+(\d{1,2})\.\s*(.*)$",
            line
        )

        if not match:
            continue

        day = int(match.group(2))
        rest = match.group(3).strip()

        title = ""

        # Monat/Jahr erkennen
        month_match = re.match(
            r"^([A-Za-zäöüÄÖÜ]+)\.?\s*(\d{2})?(.*)$",
            rest
        )

        if month_match:
            maybe_month = normalize_month(month_match.group(1))

            if maybe_month in MONTHS:
                current_month = MONTHS[maybe_month]

                if month_match.group(2):
                    current_year = 2000 + int(month_match.group(2))

                title = clean_text(month_match.group(3))
            else:
                title = clean_text(rest)
        else:
            title = clean_text(rest)

        if current_year is None or current_month is None:
            raise ValueError(f"Monat/Jahr unbekannt bei Zeile: {line}")

        start_date = format_date(current_year, current_month, day)

        # =====================================================
        # LEERER TERMIN = KLUBABEND
        # =====================================================

        if title == "":
            events.append(
                create_event(
                    title="Klubabend",
                    start_date=start_date,
                    start_time="20:00:00",
                    category=CATEGORY_KLUBABEND,
                )
            )

            continue

        # =====================================================
        # KOMBINIERTE EVENTS
        # =====================================================

        split_titles = split_combined_events(title)

        for single_title in split_titles:
            category = detect_category(single_title)

            events.append(
                create_event(
                    title=single_title,
                    start_date=start_date,
                    category=category,
                )
            )

    return events


def write_csv(events, path):

    fields = [
        "title",
        "startdate",
        "enddate",
        "starttime",
        "location",
        "content",
        "category_slugs",
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:

        # Genau wie im Beispiel
        f.write('"sep=,"\n')

        # Header
        f.write(",".join(f'"{field}"' for field in fields) + "\n")

        for event in events:

            row = []

            for field in fields:

                value = event.get(field, "")

                # Datums-/Zeitfelder NICHT quoten
                if field in ["startdate", "enddate", "starttime"]:
                    row.append(value)

                else:
                    escaped = str(value).replace('"', '""')
                    row.append(f'"{escaped}"')

            f.write(",".join(row) + "\n")


if __name__ == "__main__":
    events = parse_file(INPUT_FILE)

    write_csv(events, OUTPUT_FILE)

    print(f"{len(events)} Events exportiert nach {OUTPUT_FILE}")