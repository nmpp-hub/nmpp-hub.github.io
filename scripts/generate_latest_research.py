"""
Generate JSON data for the latest research slideshow (publications and dissertations).
This script combines recent publications and dissertations into a single JSON file
that can be used by the homepage slideshow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_generation import load_yaml, publication_base_slug, dissertation_slug

ROOT = Path(__file__).resolve().parent.parent
DISSERTATIONS_FILE = ROOT / "data" / "dissertations.yml"
PUBLICATIONS_CACHE_FILE = ROOT / "data" / ".publications_cache.json"
OUTPUT_FILE = ROOT / "data" / "latest_research.json"


def load_publications_cache() -> dict:
    """Load the publications cache file."""
    if not PUBLICATIONS_CACHE_FILE.exists():
        return {}
    
    with open(PUBLICATIONS_CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_latest_publications(cache: dict | list, limit: int = 3) -> list[dict]:
    """Extract latest publications from cache, sorted by year."""
    publications = []
    
    # Handle both dict and list cache formats
    cache_items = cache.items() if isinstance(cache, dict) else cache
    
    for item in cache_items:
        if isinstance(item, tuple):
            doi, data = item
        else:
            data = item
            doi = data.get('doi', '')
        
        year = data.get('year')
        title = data.get('title', 'Untitled Publication')
        
        # Try to get a clean title without HTML tags
        if isinstance(title, str):
            # Remove HTML tags if present
            import re
            title = re.sub('<[^<]+?>', '', title)
        
        # Generate slug for internal link
        slug = publication_base_slug(title, doi)
        
        publications.append({
            'type': 'publication',
            'doi': doi,
            'slug': slug,
            'title': title,
            'year': year,
            'authors': data.get('authors', []),
            'abstract': data.get('abstract', ''),
            'url': f"/publications/{slug}/",
        })
    
    # Sort by year descending
    publications.sort(key=lambda x: x.get('year', 0), reverse=True)
    return publications[:limit]


def extract_latest_dissertations(dissertations_data: dict, limit: int = 3) -> list[dict]:
    """Extract latest dissertations, sorted by year."""
    dissertations = []
    
    for entry in dissertations_data.get('dissertations', []):
        year = entry.get('year')
        title = entry.get('title', 'Untitled Dissertation')
        author = entry.get('author', 'Unknown')
        degree = entry.get('degree', 'phd').upper()
        
        # Generate slug for internal link
        slug = dissertation_slug(entry)
        
        dissertations.append({
            'type': 'dissertation',
            'title': title,
            'slug': slug,
            'author': author,
            'degree': degree,
            'year': year,
            'link': f"/dissertations/{slug}/",
            'abstract': f"{degree} thesis by {author}",
        })
    
    # Sort by year descending
    dissertations.sort(key=lambda x: x.get('year', 0), reverse=True)
    return dissertations[:limit]


def generate_slideshow_data(max_items: int = 6) -> list[dict]:
    """Generate combined and sorted list of latest research items."""
    # Load data
    publications_cache = load_publications_cache()
    dissertations_data = load_yaml(DISSERTATIONS_FILE)
    
    # Extract items
    publications = extract_latest_publications(publications_cache)
    dissertations = extract_latest_dissertations(dissertations_data)
    
    # Combine and sort by year
    all_items = publications + dissertations
    all_items.sort(key=lambda x: x.get('year', 0), reverse=True)
    
    # Return top N items
    return all_items[:max_items]


def main():
    parser = argparse.ArgumentParser(
        description='Generate latest research slideshow data from publications and dissertations.'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=6,
        help='Maximum number of items to include (default: 6)'
    )
    args = parser.parse_args()
    
    # Generate data
    slideshow_data = generate_slideshow_data(max_items=args.limit)
    
    # Write to output file
    output_data = {
        'items': slideshow_data,
        'generated': True,
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(slideshow_data)} latest research items")
    print(f"Output written to {OUTPUT_FILE}")
    
    if slideshow_data:
        print("\nFirst item preview:")
        item = slideshow_data[0]
        print(f"  Type: {item['type']}")
        print(f"  Title: {item['title'][:60]}...")
        print(f"  Year: {item['year']}")


if __name__ == '__main__':
    main()
