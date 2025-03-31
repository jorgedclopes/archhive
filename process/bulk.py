from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

from process.db import PGDB

BATCH_SIZE = 10000
MAX_WORKERS = 16  # Adjust based on CPU & DB performance


db = PGDB()


def parse_large_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if isinstance(entry, dict):
                yield entry


def process_entry(entry):
    return (
        entry["title"],
        entry["authors"].split(", "),
        entry["id"],
        next((v["created"] for v in entry["versions"] if v["version"] == "v1"), None),
        (
            datetime.fromisoformat(entry["update_date"]).date()
            if "update_date" in entry
            else None
        ),
        datetime.now(),
        entry["abstract"],
        entry.get("comments"),
        None,  # primary_category (optional)
        entry["categories"],
    )


def insert_worker(db, entry):
    try:
        db.insert_article(entry)
    except TypeError as e:
        print(e)


if __name__ == "__main__":  # Change to your desired category
    path = "/home/jorge/Downloads/arxiv-metadata-oai-snapshot.json"

    batch = []
    futures = []
    c = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for entry in parse_large_json(path):
            c += 1
            if c < 0:
                continue

            batch.append(process_entry(entry))
            if len(batch) >= BATCH_SIZE:
                futures.append(
                    executor.submit(insert_worker, db, batch[:])
                )  # Copy batch
                batch.clear()
                for future in as_completed(futures):
                    future.result()
                db.connection.commit()
            if batch:
                futures.append(executor.submit(insert_worker, db, batch))

            if c % 1000 == 0:
                print(f"{c} inserted")
