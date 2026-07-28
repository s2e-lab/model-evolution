from pathlib import Path

import pandas as pd

from utils import DATA_DIR
from get_commit_logs import load_cache, save_to_cache


csv_path = DATA_DIR / "v1_selected_recent/repositories_evolution_recent_commits.csv"
cache_path = DATA_DIR / "_commit_analysis_cache.sqlite3"

df = pd.read_csv(csv_path)
load_cache(cache_path)

commit_columns = [
    "commit_hash",
    "author",
    "date",
    "message",
    "changed_files",
    "all_files_in_tree",
]

for repo_url, df_repo in df.groupby("repo_url"):
    # Replace pandas NaN values with empty strings so JSON serialization
    # produces valid cached values.
    df_repo = df_repo.fillna("")

    repo_commits = list(
        df_repo[commit_columns].itertuples(index=False, name=None)
    )

    save_to_cache(cache_path, repo_url, repo_commits)

print(f"Loaded commits for {df['repo_url'].nunique()} repositories into {cache_path}")