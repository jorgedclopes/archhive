import time
from typing import Optional

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from process.db import PGDB


db = PGDB()


def get_arxiv_papers(
    category, batch_size=100, t=4, target_date: Optional[datetime] = None
) -> None:
    """
    Fetch all arXiv articles for a specific date with pagination.

    :param category: arXiv category (e.g., 'cs.LG')
    :param batch_size: Number of articles per request (adjust for efficiency)
    :param t: time to sleep between API calls
    :param target_date: if present breaks the loop
    :return: List of (title, authors, link, published_date)
    """
    base_url = "http://export.arxiv.org/api/query"

    ns = {
        "arxiv": "http://www.w3.org/2005/Atom",
        "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
        "arxiv_schema": "http://arxiv.org/schemas/atom",
    }
    start = 0

    while True:
        # Construct query URL with pagination
        url = f"{base_url}?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&start={start}&max_results={batch_size}"
        print(f"Fetching between {start} and {start + batch_size}.")
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.HTTPError:
            print("Error fetching data")
            break

        # Parse XML
        root = ET.fromstring(response.text)
        total_results = int(root.find("opensearch:totalResults", ns).text)

        found_papers = 0
        for entry in root.findall("arxiv:entry", ns):
            title = entry.find("arxiv:title", ns).text.strip()
            link = entry.find("arxiv:id", ns).text.strip()
            published_date = datetime.strptime(
                entry.find("arxiv:published", ns).text, "%Y-%m-%dT%H:%M:%SZ"
            ).date()  # check the datetimes
            updated_date = datetime.strptime(
                entry.find("arxiv:updated", ns).text, "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            inserted = datetime.now()

            # Extract authors as a list
            authors = [
                author.find("arxiv:name", ns).text.strip()
                for author in entry.findall("arxiv:author", ns)
            ]
            summary = entry.find("arxiv:summary", ns).text
            comment = entry.find("arxiv_schema:comment", ns)
            comment = comment.text.strip() if comment is not None else None
            categories = [c.get("term") for c in entry.findall("arxiv:category", ns)]

            db.insert_article(
                title,
                authors,
                link,
                published_date,
                updated_date,
                inserted,
                summary,
                comment,
                category,
                categories,
            )
            found_papers += 1

            if target_date and target_date > published_date:
                print(f"{target_date} > {published_date}")
                return

        print(f"{found_papers=}")
        if start + batch_size >= total_results:  # or found_papers == 0:
            print(f"{start + batch_size} >= {total_results}")
            return

        if found_papers == batch_size:
            start += batch_size  # Next batch
        time.sleep(t)


# Example Usage
if __name__ == "__main__":
    category = "cs.LG"  # Change to your desired category
    get_arxiv_papers(category)
