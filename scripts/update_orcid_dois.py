#!/usr/bin/env python3
"""
Fetch publications from ORCID for all permanent staff and professor members
and add their DOIs to data/dois.yml (respecting start_date and end_date if present).
"""

from datetime import datetime
from pathlib import Path

import requests
import yaml

try:
    from dateutil import parser as date_parser
except ImportError:
    print("Error: dateutil is required. Install with: pip install python-dateutil")
    exit(1)

ORCID_API_URL_TEMPLATE = "https://pub.orcid.org/v3.0/{orcid}/works"


def load_members():
    """Load members from data/members.yml and filter for eligible ones."""
    members_file = Path(__file__).parent.parent / "data" / "members.yml"

    if not members_file.exists():
        print(f"Error: {members_file} not found")
        return []

    with open(members_file, "r") as f:
        data = yaml.safe_load(f)

    eligible = []
    for member in data.get("members", []):
        role = member.get("role", "").lower()
        orcid = member.get("orcid")

        # Include if role is professor or permanent staff, has ORCID, and has start_date
        if orcid and (role == "professor" or role == "group leader"):
            if not member.get("start_date"):
                continue  # Skip members without start_date
            eligible.append(
                {
                    "name": member.get("name", "Unknown"),
                    "orcid": orcid,
                    "start_date": member.get("start_date"),
                    "end_date": member.get("end_date"),
                }
            )

    return eligible


def fetch_orcid_publications(orcid_id):
    """Fetch all publications from ORCID for the given ORCID ID."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "NMPP-Hub/1.0 (+https://nmpp-hub.github.io)",
    }

    url = ORCID_API_URL_TEMPLATE.format(orcid=orcid_id)

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("group", [])
    except requests.RequestException as e:
        print(f"  Error fetching ORCID data: {e}")
        return []


def parse_date(date_str):
    """Parse a date string to a datetime object."""
    if not date_str:
        return None
    try:
        return date_parser.parse(str(date_str))
    except (ValueError, TypeError):
        return None


def extract_dois(orcid_works, start_date=None, end_date=None):
    """Extract DOIs from ORCID works, filtering by date range if provided."""
    dois = {}

    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    for group in orcid_works:
        work = group.get("work-summary", [{}])[0]

        # Get publication date
        pub_date_obj = work.get("publication-date")
        if not pub_date_obj:
            pub_date_obj = {}

        year_str = None
        month_str = "01"
        day_str = "01"

        year_obj = pub_date_obj.get("year")
        if year_obj:
            year_str = year_obj.get("value")

        month_obj = pub_date_obj.get("month")
        if month_obj:
            month_str = month_obj.get("value", "01")

        day_obj = pub_date_obj.get("day")
        if day_obj:
            day_str = day_obj.get("value", "01")

        pub_date = None
        if year_str:
            try:
                pub_date = datetime(int(year_str), int(month_str), int(day_str))
            except (ValueError, TypeError):
                pass

        # Filter by date range
        if pub_date:
            if start_dt and pub_date < start_dt:
                continue
            if end_dt and pub_date > end_dt:
                continue
        elif start_dt or end_dt:
            # Skip if we have date filters but no publication date
            continue

        # Extract DOI from external IDs
        external_ids = work.get("external-ids", {}).get("external-id", [])
        for ext_id in external_ids:
            if ext_id.get("external-id-type", "").lower() == "doi":
                doi = ext_id.get("external-id-value")
                if doi:
                    # Normalize DOI to lowercase
                    doi = doi.lower()
                    title = work.get("title", {}).get("title", {}).get("value", "")
                    dois[doi] = {"title": title if title else None}

    return dois


def load_current_dois():
    """Load existing DOIs from data/dois.yml"""
    dois_file = Path(__file__).parent.parent / "data" / "dois.yml"

    if not dois_file.exists():
        print(f"Error: {dois_file} not found")
        return {}

    with open(dois_file, "r") as f:
        data = yaml.safe_load(f)

    current_dois = {}
    for pub in data.get("publications", []):
        doi = pub.get("doi", "").lower()
        if doi:
            current_dois[doi] = pub

    return current_dois


def save_dois(dois_dict):
    """Save DOIs back to data/dois.yml"""
    dois_file = Path(__file__).parent.parent / "data" / "dois.yml"

    publications = []
    for doi in sorted(dois_dict.keys()):
        pub = dois_dict[doi]
        entry = {"doi": pub["doi"]}
        if pub.get("title"):
            entry["title"] = pub["title"]
        if pub.get("codes"):
            entry["codes"] = pub["codes"]
        publications.append(entry)

    data = {"publications": publications}

    with open(dois_file, "w") as f:
        f.write("# DOI input file.\n")
        f.write("# Each entry under 'publications:' defines a publication by DOI.\n")
        f.write("# Fields:\n")
        f.write("#   doi: required publication DOI\n")
        f.write("#   title: optional title for human-readable context\n")
        f.write(
            "#   codes: optional list of code slugs associated with the publication\n"
        )
        f.write("#\n")
        f.write(
            "# Use this file to add DOI metadata for publications. The generator fetches details automatically.\n"
        )
        f.write("# After editing, run generate_website.py to update the website.\n")
        f.write("#\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def main():
    print("Loading eligible members from members.yml...")
    members = load_members()

    if not members:
        print(
            "No eligible members found (must be professor/group leader with ORCID and start_date)"
        )
        return

    print(f"Found {len(members)} eligible members\n")

    # Load existing DOIs
    current_dois = load_current_dois()
    print(f"Currently have {len(current_dois)} DOIs in data/dois.yml\n")

    total_added = 0

    for member in members:
        name = member["name"]
        orcid = member["orcid"]
        start_date = member.get("start_date")
        end_date = member.get("end_date")

        date_range = ""
        if start_date or end_date:
            date_range = f" ({start_date or '?'} - {end_date or '?'})"

        print(f"Fetching publications for {name} ({orcid}){date_range}...")

        # Fetch from ORCID
        orcid_works = fetch_orcid_publications(orcid)
        if not orcid_works:
            print(f"  No publications found")
            continue

        # Extract DOIs with date filtering
        new_dois = extract_dois(orcid_works, start_date, end_date)
        print(f"  Found {len(new_dois)} publications with DOIs")

        # Find new DOIs to add
        added = 0
        for doi, data in new_dois.items():
            if doi not in current_dois:
                current_dois[doi] = {"doi": doi, "title": data["title"]}
                added += 1
                print(f"    + {doi}")

        if added > 0:
            total_added += added
            print(f"  Added {added} new DOI(s)\n")
        else:
            print(f"  No new DOIs to add\n")

    if total_added > 0:
        print(f"Saving {total_added} new DOI(s) to data/dois.yml...")
        save_dois(current_dois)
        print("Done!")
    else:
        print("No new DOIs to add")


if __name__ == "__main__":
    main()
