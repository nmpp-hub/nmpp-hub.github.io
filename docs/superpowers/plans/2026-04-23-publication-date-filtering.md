# Date Range Filtering for Publications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add publication date range filtering to both ORCID and Pure article fetching so only articles published during a member's employment period are included in their publication lists.

**Architecture:** Both scripts will filter articles based on member `start_date` and `end_date` fields. Members without both dates will be skipped (conservative approach). Pure script gains date parsing logic to match ORCID behavior. Articles without publication dates generate warnings. Only articles within the date range are added to the database.

**Tech Stack:** Python 3, dateutil, YAML, REST APIs

---

## File Structure

**Files to modify:**
- `scripts/fetch_pure_dois.py` - Add date range filtering with date parsing
- `scripts/update_orcid_dois.py` - Add check to skip members without start_date
- `data/members.yml` - Update comments to document date filtering behavior

---

## Implementation Tasks

### Task 1: Update Pure Script to Parse Publication Dates

**Files:**
- Modify: `scripts/fetch_pure_dois.py` (extract_dois_from_pure function)

**Context:** The Pure API returns publication dates in metadata. We need to extract and parse these to filter by date range, just like ORCID does.

- [ ] **Step 1: Add dateutil import and date parsing helper**

In `scripts/fetch_pure_dois.py`, update the imports section to add dateutil:

```python
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
```

Then add a helper function to parse dates (add this right after the PURE_API_URL constant):

```python
def parse_date(date_str):
    """Parse a date string to a datetime object."""
    if not date_str:
        return None
    try:
        return date_parser.parse(str(date_str))
    except (ValueError, TypeError):
        return None
```

- [ ] **Step 2: Update extract_dois_from_pure signature to accept date parameters**

Change the function signature from:
```python
def extract_dois_from_pure(records: list) -> dict[str, dict]:
```

To:
```python
def extract_dois_from_pure(records: list, start_date=None, end_date=None) -> dict[str, dict]:
```

And update the docstring:
```python
    """
    Extract DOI and title from Pure records, filtering by date range if provided.
    
    Returns dict mapping DOI -> {"title": str}
    
    DOIs are stored in metadata.identifiers with type 'DOI'.
    Field structure: {"id": "10.xxxx/yyyy", "type": "DOI"}
    """
```

- [ ] **Step 3: Add date parsing logic inside extract_dois_from_pure**

Inside the function, right after `dois = {}`, add:

```python
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
```

- [ ] **Step 4: Add date filtering in the record loop**

Inside the `for record in records:` loop, right after extracting title and before the identifiers loop, add:

```python
            # Get publication date from metadata
            pub_date_str = metadata.get("datePublished") or metadata.get("datePublishedInPrint")
            pub_date = None
            if pub_date_str:
                try:
                    pub_date = parse_date(pub_date_str)
                except (ValueError, TypeError):
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
```

- [ ] **Step 5: Update main() to pass dates to extract function**

In the `main()` function, find the line:
```python
        # Extract DOIs
        new_dois = extract_dois_from_pure(records)
```

Replace with:
```python
        # Extract DOIs
        new_dois = extract_dois_from_pure(
            records, 
            start_date=member.get("start_date"),
            end_date=member.get("end_date")
        )
```

- [ ] **Step 6: Verify syntax**

Run: `python -m py_compile scripts/fetch_pure_dois.py`

Expected: No output (syntax is valid)

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch_pure_dois.py
git commit -m "feat: add publication date range filtering to Pure DOI extraction"
```

---

### Task 2: Update ORCID Script to Skip Members Without Date Range

**Files:**
- Modify: `scripts/update_orcid_dois.py` (load_members function)

**Context:** Currently ORCID script processes all members with ORCID, but only applies date filtering IF they have start/end dates. For consistency with Pure filtering, members without both dates should be skipped entirely.

- [ ] **Step 1: Update load_members to require both dates**

In `scripts/update_orcid_dois.py`, find the `load_members()` function. Update the eligibility check from:

```python
        # Include if role is professor or permanent staff AND has ORCID
        if orcid and (role == "professor" or role == "group leader"):
```

To:

```python
        # Include if role is professor or permanent staff, has ORCID, and has start_date
        if orcid and (role == "professor" or role == "group leader"):
            if not member.get("start_date"):
                continue  # Skip members without start_date
```

- [ ] **Step 2: Add message about filtered members**

In the `main()` function, after printing the eligible members count, add:

```python
    if not members:
        print(
            "No eligible members found (must be professor/group leader with ORCID and start_date)"
        )
        return
```

- [ ] **Step 3: Verify syntax**

Run: `python -m py_compile scripts/update_orcid_dois.py`

Expected: No output (syntax is valid)

- [ ] **Step 4: Test ORCID script**

Run: `python scripts/update_orcid_dois.py`

Expected: Script runs and processes only eligible members (those with ORCID, professor/group leader role, and start_date)

- [ ] **Step 5: Commit**

```bash
git add scripts/update_orcid_dois.py
git commit -m "feat: require start_date for ORCID article filtering"
```

---

### Task 3: Update Members.yml Comments

**Files:**
- Modify: `data/members.yml` (comments section)

**Context:** Document the new date filtering behavior so users understand why articles might not be included.

- [ ] **Step 1: Update the members.yml header comments**

In `data/members.yml`, find the comments section at the top. Update it to add documentation about start_date and end_date filtering. Change the section from:

```yaml
# Member page input file.
# Each entry under 'members:' defines a person with optional profile data.
# Fields:
#   name: required display name
#   role: role/position like professor, postdoc, phd, alumni
#   topic: short research topic or focus area
#   contact: email address or other contact
#   group: group name from groups.yml
#   codes: list of code slugs to link this member with codes
#   alumni: true/false
#   aliases: alternative names used for matching publications/dissertations
#   picture: URL or path to a profile image
#   description: short bio or research summary
#   github, gitlab, google_scholar, orcid, linkedin, website, researchgate,
#   twitter, x, bluesky, mastodon, academia_edu, semanticscholar, dblp:
#     optional profile identifiers or URLs for social/academic links
```

To:

```yaml
# Member page input file.
# Each entry under 'members:' defines a person with optional profile data.
# Fields:
#   name: required display name
#   role: role/position like professor, postdoc, phd, alumni
#   topic: short research topic or focus area
#   contact: email address or other contact
#   group: group name from groups.yml
#   codes: list of code slugs to link this member with codes
#   alumni: true/false
#   aliases: alternative names used for matching publications/dissertations
#   picture: URL or path to a profile image
#   description: short bio or research summary
#   start_date, end_date: optional dates (YYYY-MM-DD format) controlling which articles are
#     attributed to the member. Only articles published within this range will be included
#     in their publication list. Required for ORCID/Pure filtering to work.
#   orcid, mpg_pure: optional publication source identifiers. If present with start_date,
#     articles will be fetched and filtered by publication date.
#   github, gitlab, google_scholar, linkedin, website, researchgate,
#   twitter, x, bluesky, mastodon, academia_edu, semanticscholar, dblp:
#     optional profile identifiers or URLs for social/academic links
```

- [ ] **Step 2: Verify YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('data/members.yml'))"`

Expected: No error (YAML is valid)

- [ ] **Step 3: Commit**

```bash
git add data/members.yml
git commit -m "docs: document start_date/end_date publication filtering behavior"
```

---

### Task 4: Test End-to-End with Date Filtering

**Files:**
- No files modified; integration testing

**Context:** Verify that date filtering works correctly for both ORCID and Pure sources.

- [ ] **Step 1: Run full generation pipeline**

Run: `python generate_website.py`

Expected: Pipeline runs successfully with both ORCID and Pure fetching steps:
```
======================================================================
Running: Update DOIs from ORCID
======================================================================
Loading eligible members from members.yml...
Found X eligible member(s)
...
======================================================================
Running: Fetch DOIs from Pure/MPG
======================================================================
Loading members with mpg_pure identifiers...
Found Y member(s) with mpg_pure
...
```

- [ ] **Step 2: Verify no build errors**

Run: `npm run build`

Expected: Build completes successfully with no errors.

- [ ] **Step 3: Verify DOIs file integrity**

Run: `python -c "import yaml; data = yaml.safe_load(open('data/dois.yml')); dois = [p['doi'] for p in data['publications']]; print(f'Total DOIs: {len(dois)}, Unique: {len(set(dois))}')"`

Expected: Total DOIs == Unique DOIs (no duplicates)

- [ ] **Step 4: Verify git status is clean**

Run: `git status`

Expected: All changes committed from previous tasks. Working directory clean.

---

## Notes

- **Date Parsing:** Both scripts use `dateutil.parser.parse()` for flexible date parsing (same as existing ORCID code)
- **Conservative Filtering:** Members without start_date are skipped entirely to ensure only intentional filtering happens
- **Warnings:** Publications without dates generate warnings so operators know what was filtered
- **Consistency:** Both ORCID and Pure now follow the same date filtering pattern
- **Backward Compatibility:** Members without dates work as before (completely skipped by ORCID; Pure not assigned to them)
