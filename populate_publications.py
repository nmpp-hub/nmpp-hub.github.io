import json
import re
import urllib.request
from pathlib import Path


def fetch_publication_metadata(doi: str) -> dict | None:
    try:
        url = f"https://doi.org/{doi}"
        req = urllib.request.Request(
            url, headers={"Accept": "application/vnd.citationstyles.csl+json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        # Extract year
        year = "Unknown"
        for key in ("published-online", "published-print", "issued"):
            if key in data and "date-parts" in data[key]:
                parts = data[key]["date-parts"]
                if parts and parts[0]:
                    year = str(parts[0][0])
                    break

        title = data.get("title", "Unknown")

        # Authors: family, given or literal
        authors = ""
        if "author" in data:
            names = []
            for a in data["author"]:
                if "family" in a:
                    name = a["family"]
                    if "given" in a:
                        name = f"{a['given']} {name}"
                    names.append(name)
                elif "literal" in a:
                    names.append(a["literal"])
                elif "name" in a:
                    names.append(a["name"])
            authors = ", ".join(names)

        # publisher
        publisher = data.get("container-title", data.get("publisher", "Unknown"))

        return {
            "year": year,
            "title": title,
            "authors": authors,
            "publisher": publisher,
            "doi": doi,
        }
    except Exception as e:
        print(f"Error fetching DOI {doi}: {e}")
        return None


def generate_table_row(pub: dict) -> str:
    return f"""        <tr>
          <td>{pub['year']}</td>
          <td>{pub['title']}</td>
          <td>{pub['authors']}</td>
          <td>{pub['publisher']}</td>
          <td><a href="https://doi.org/{pub['doi']}">DOI</a></td>
        </tr>"""


def main(dois_file: Path, publications_file: Path):
    # Read DOIs and remove duplicates while preserving order
    dois = []
    seen = set()
    with open(dois_file) as f:
        for line in f:
            doi = line.strip()
            if doi and doi not in seen:
                dois.append(doi)
                seen.add(doi)

    print(f"Found {len(dois)} unique DOIs")

    # Fetch metadata for all DOIs
    publications = []
    for i, doi in enumerate(dois, 1):
        print(f"[{i}/{len(dois)}] Fetching {doi}...", end=" ", flush=True)
        pub = fetch_publication_metadata(doi)
        if pub:
            publications.append(pub)
            print(" - ok")
        else:
            print(" - failed")

    # Sort by year descending
    publications.sort(key=lambda x: x["year"], reverse=True)

    # Read the existing publications file
    with open(publications_file) as f:
        content = f.read()

    # Generate table rows
    rows = "\n".join(generate_table_row(pub) for pub in publications)

    # Replace the tbody content
    new_content = re.sub(
        r"(<tbody>).*?(</tbody>)",
        f"\\1\n{rows}\n      \\2",
        content,
        flags=re.DOTALL,
    )

    with open(publications_file, "w") as f:
        f.write(new_content)

    print(f"\nUpdated {publications_file} with {len(publications)} publications")


if __name__ == "__main__":
    main(Path("dois.txt"), Path("src/pages/publications.astro"))
