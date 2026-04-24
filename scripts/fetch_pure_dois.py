#!/usr/bin/env python3
"""
Fetch publications from Pure/MPG for members with mpg_pure identifier
and add their DOIs to data/dois.yml (avoiding duplicates with ORCID).
"""

from pathlib import Path
from typing import Any
from datetime import datetime

import requests
import yaml

try:
    from dateutil import parser as date_parser
except ImportError:
    print("Error: dateutil is required. Install with: pip install python-dateutil")
    exit(1)

PURE_API_URL = "https://pure.mpg.de/rest/items/search?format=json"


def parse_date(date_str):
    """Parse a date string to a datetime object."""
    if not date_str:
        return None
    try:
        return date_parser.parse(str(date_str))
    except (ValueError, TypeError):
        return None


def load_members():
    """Load members from data/members.yml and filter for those with mpg_pure."""
    members_file = Path(__file__).parent.parent / "data" / "members.yml"

    if not members_file.exists():
        print(f"Error: {members_file} not found")
        return []

    with open(members_file, "r") as f:
        data = yaml.safe_load(f)

    eligible = []
    for member in data.get("members", []):
        mpg_pure_id = member.get("mpg_pure")
        if mpg_pure_id:
            if not member.get("start_date"):
                continue  # Skip members without start_date
            eligible.append(
                {
                    "name": member.get("name", "Unknown"),
                    "mpg_pure": mpg_pure_id,
                    "start_date": member.get("start_date"),
                    "end_date": member.get("end_date"),
                }
            )

    return eligible


def fetch_pure_publications(mpg_pure_id: str) -> dict[str, Any]:
    """
    Fetch publications from Pure API for the given person identifier.
    Returns dict with 'records' key containing list of publications.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NMPP-Hub/1.0 (+https://nmpp-hub.github.io)",
    }

    payload = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"publicState": {"value": "RELEASED"}}},
                    {"term": {"versionState": {"value": "RELEASED"}}},
                    {
                        "term": {
                            "metadata.creators.person.identifier.id": {
                                "value": f"/persons/resource/{mpg_pure_id}"
                            }
                        }
                    },
                ]
            }
        },
        "sort": [{"sort-metadata-dates-by-category": {"order": "desc"}}],
        "size": 50,
        "from": 0,
    }

    try:
        response = requests.post(url=PURE_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"  Error fetching Pure data: {e}")
        return {}


def extract_dois_from_pure(records: list, start_date=None, end_date=None) -> dict[str, dict]:
    """
    Extract DOI and title from Pure records, filtering by date range if provided.
    
    Returns dict mapping DOI -> {"title": str}
    
    DOIs are stored in metadata.identifiers with type 'DOI'.
    Field structure: {"id": "10.xxxx/yyyy", "type": "DOI"}
    """
    dois = {}

    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)

    for record in records:
        try:
            metadata = record.get("data", {}).get("metadata", {})
            title = metadata.get("title", "")
            
            # Get publication date from metadata
            # Try multiple date fields, in order of preference
            pub_date_str = (
                metadata.get("datePublished") 
                or metadata.get("datePublishedInPrint") 
                or metadata.get("datePublishedOnline")
                or metadata.get("dateCreated")
                or metadata.get("dateSubmitted")
            )
            pub_date = None
            if pub_date_str:
                pub_date = parse_date(pub_date_str)
                if not pub_date:
                    print(f"    Warning: Could not parse publication date: {pub_date_str}")
                    continue
            
            # Filter by date range
            if start_dt or end_dt:
                if not pub_date:
                    print(f"    Warning: No publication date found, skipping article")
                    continue
                if start_dt and pub_date < start_dt:
                    continue
                if end_dt and pub_date > end_dt:
                    continue
            
            # Extract DOI from identifiers array
            identifiers = metadata.get("identifiers", [])
            for identifier in identifiers:
                if identifier.get("type", "").upper() == "DOI":
                    doi = identifier.get("id", "").lower()
                    if doi:
                        dois[doi] = {"title": title if title else None}
                    break  # Only take first DOI per record
        except (KeyError, AttributeError, TypeError):
            # Skip malformed records
            continue

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


def save_dois(dois_dict: dict):
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
    print("Loading members with mpg_pure identifiers...")
    members = load_members()

    if not members:
        print("No members with mpg_pure identifier found (must have mpg_pure and start_date)")
        return

    print(f"Found {len(members)} member(s) with mpg_pure\n")

    # Load existing DOIs to avoid duplicates
    current_dois = load_current_dois()
    print(f"Currently have {len(current_dois)} DOIs in data/dois.yml\n")

    total_added = 0

    for member in members:
        name = member["name"]
        mpg_pure_id = member["mpg_pure"]

        print(f"Fetching publications for {name} (Pure ID: {mpg_pure_id})...")

        # Fetch from Pure
        response_data = fetch_pure_publications(mpg_pure_id)
        records = response_data.get("records", [])

        if not records:
            print(f"  No publications found\n")
            continue

        # Extract DOIs
        new_dois = extract_dois_from_pure(
            records, 
            start_date=member.get("start_date"),
            end_date=member.get("end_date")
        )
        print(f"  Found {len(new_dois)} publications with DOIs")

        # Find new DOIs to add (skip duplicates)
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
