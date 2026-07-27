"""
get_repo_pr_baseline.py

PR baseline: for each repo that received an SFConvertBot conversion PR,
list ALL its PRs and split into conversion (SFConvertbot) vs other (everyone
else), tallying merge status. Lets us compare the "other PR" merge rate on
these same repos against the 13.9% conversion-PR rate.

Follows the same loop and save_checkpoint pattern as get_conversions_dataset.py.
The only new piece vs. existing scripts is list_repo_prs(), which enumerates a
repo's PRs (existing scripts all start from a URL/row we already have; this
one starts from a repo and discovers its PRs).
"""
import os
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from huggingface_hub import get_repo_discussions

from bot_utils import save_checkpoint  

DATA_DIR = Path('../../data')
BOT = "sfconvertbot"  # author name of conversion PRs (lowercased for matching)


def list_repo_prs(repo_id: str) -> list:
    """
    NEW capability: given a repo, return one dict per PR with author-bucket
    and status. 
    Returns [] and lets caller record an error on failure.
    """
    rows = []
    for d in get_repo_discussions(repo_id, repo_type="model"):
        # only interested in pull requests
        if not d.is_pull_request:
            continue
        rows.append({
            "model_id": repo_id,
            "num": d.num,
            "is_conversion": (d.author or "").lower() == BOT,
            "status": (d.status or "").lower(),   # open / merged / closed / draft
        })
    return rows


if __name__ == '__main__':
    save_at = 500
    out_file_prefix = 'repo_pr_baseline'

    # Repo list = unique model_id from the metadata
    meta = pd.read_csv(DATA_DIR / 'sfconvertbot_pr_metadata.csv',
                       usecols=['model_id'])
    repos = meta['model_id'].dropna().astype(str).drop_duplicates().tolist()

    all_rows, errors = [], []
    for i, repo_id in enumerate(tqdm(repos, total=len(repos), unit='repo')):
        try:
            all_rows.extend(list_repo_prs(repo_id))
        except Exception as e:                    # keep the crawl alive
            errors.append({"model_id": repo_id, "error": f"{type(e).__name__}:{e}"})

        if i != 0 and i % save_at == 0:
            save_checkpoint(pd.DataFrame(all_rows), out_file_prefix, i, save_at)

    pd.DataFrame(all_rows).to_csv(DATA_DIR / f'{out_file_prefix}.csv', index=False)
    pd.DataFrame(errors).to_csv(DATA_DIR / f'{out_file_prefix}_errors.csv', index=False)

    # delete leftover checkpoints (same tidy-up as get_conversions_dataset.py)
    for i in range(save_at, len(repos), save_at):
        f = DATA_DIR / f'{out_file_prefix}_{i}.csv'
        if f.exists():
            os.remove(f)
