import sqlite3

from utils import DATA_DIR
from analyze_commit_history import load_cache

# Source database containing newer cached results.
new_cache = DATA_DIR / "_GAMING_commit_analysis_cache.sqlite3"

# Destination database containing the existing cached results.
cache_path = DATA_DIR / "_commit_analysis_cache.sqlite3"

if not new_cache.exists():
    raise FileNotFoundError(f"New cache does not exist: {new_cache}")

# Ensure the destination cache and its table exist.
load_cache(cache_path)

with sqlite3.connect(cache_path) as connection:
    connection.execute(
        "ATTACH DATABASE ? AS new_cache",
        (str(new_cache),),
    )

    before_count = connection.execute(
        "SELECT COUNT(*) FROM analysis_cache"
    ).fetchone()[0]

    # Insert only rows whose (repo_url, commit_hash) primary key
    # does not already exist in the destination cache.
    connection.execute("""
        INSERT OR IGNORE INTO analysis_cache (
            repo_url,
            commit_hash,
            results,
            updated_at
        )
        SELECT
            repo_url,
            commit_hash,
            results,
            updated_at
        FROM new_cache.analysis_cache
    """)

    after_count = connection.execute(
        "SELECT COUNT(*) FROM analysis_cache"
    ).fetchone()[0]

    connection.commit()
    connection.execute("DETACH DATABASE new_cache")

inserted_count = after_count - before_count

print(f"Inserted {inserted_count} missing commits into {cache_path}")
print(f"Destination cache now contains {after_count} commits")