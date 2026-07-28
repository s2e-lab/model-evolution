import pandas as pd

from utils import DATA_DIR
from analyze_commit_history import load_cache, save_to_cache

csv_path = DATA_DIR / "v1_selected_recent/repositories_evolution_recent_commits.csv"
cache_path = DATA_DIR / "_commit_analysis_cache.sqlite3"

df = pd.read_csv(csv_path).fillna("")

load_cache(cache_path)

result_columns = [
    "repo_url",
    "commit_hash",
    "model_file_path",
    "serialization_format",
    "message",
    "author",
    "date",
    "is_in_commit",
]

num_commits = 0

for (repo_url, commit_hash), df_commit in df.groupby(
    ["repo_url", "commit_hash"],
    sort=False,
):
    commit_results = df_commit[result_columns].to_dict("records")

    save_to_cache(
        cache_path,
        repo_url,
        commit_hash,
        commit_results,
    )

    num_commits += 1

print(
    f"Loaded {num_commits} commits "
    f"from {df['repo_url'].nunique()} repositories into {cache_path}"
)