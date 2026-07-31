import argparse
import atexit
import logging
import os
import sys
from pathlib import Path
import sqlite3
import pandas as pd
import json
from tqdm import tqdm

from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection, SerializationMethod
from analyticaml.model_parser import detect_serialization_format
from utils import DATA_DIR, download_model_files, get_file_extension, get_tmp_folder, enforce_ssh
from utils import delete_folder

DOWNLOAD_TIMEOUT = 20 # timout in seconds

# configure logger
DEBUG = False
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def load_cache(cache_path: Path) -> None:
    with sqlite3.connect(cache_path) as connection:
        fields = ",".join([
            "repo_url TEXT NOT NULL",
            "commit_hash TEXT NOT NULL",
            "results TEXT NOT NULL",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ])
        pk = "repo_url, commit_hash"
        connection.execute(f"CREATE TABLE IF NOT EXISTS analysis_cache ({fields}, PRIMARY KEY({pk}))")


def load_cache_in_memory(cache_path: Path, df_slice: pd.DataFrame) -> dict[tuple[str, str], list]:
    keys = list(
        df_slice[["repo_url", "commit_hash"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    with sqlite3.connect(cache_path) as connection:
        connection.execute("""CREATE TEMP TABLE requested_commits (
                repo_url TEXT NOT NULL,
                commit_hash TEXT NOT NULL,
                PRIMARY KEY (repo_url, commit_hash)
            )""")

        connection.executemany("INSERT OR IGNORE INTO requested_commits (repo_url, commit_hash) VALUES (?, ?)",
            keys,
        )

        rows = connection.execute("""
                                  SELECT cache.repo_url,
                                         cache.commit_hash,
                                         cache.results
                                  FROM analysis_cache AS cache
                                           INNER JOIN requested_commits AS requested
                                                      ON cache.repo_url = requested.repo_url
                                                          AND cache.commit_hash = requested.commit_hash
                                  """).fetchall()

    return {
        (repo_url, commit_hash): json.loads(results)
        for repo_url, commit_hash, results in rows
    }


def get_cached_analysis(cache_path: Path, repo_url: str, commit_hash: str, ) -> list | None:
    with sqlite3.connect(cache_path) as connection:
        row = connection.execute(
            "SELECT results FROM analysis_cache WHERE repo_url = ? AND commit_hash = ?",
            (repo_url, commit_hash),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row[0])


def save_to_cache(cache_path: Path, repo_url: str, commit_hash: str, results: list, ) -> None:
    with sqlite3.connect(cache_path) as connection:
        connection.execute("""
                           INSERT INTO analysis_cache (repo_url, commit_hash, results, updated_at)
                           VALUES (?, ?, ?, CURRENT_TIMESTAMP) ON CONFLICT(repo_url, commit_hash) DO
                           UPDATE SET
                               results = excluded.results,
                               updated_at = CURRENT_TIMESTAMP
                           """, (repo_url, commit_hash, json.dumps(results, default=str),)
                           )


def parse_args():
    """
    Parse the command line arguments
    :return: the parsed arguments
    """
    parser = argparse.ArgumentParser(description="Process repository group.")
    parser.add_argument("--group_type", required=True, choices=["legacy", "recent"], help="Choices: 'legacy' or 'recent'.")
    parser.add_argument("--begin", type=int, default=None, help="Starting row index (inclusive).")
    parser.add_argument("--end", type=int, default=None, help="Ending row index (exclusive).")
    return parser.parse_args()


def filter_by_extension(changed_files: str):
    """
    Implement a filter to check if the list of changed files in a commit has model files.
    A model file is a file that has one of the extensions in MODEL_FILE_EXTENSIONS.
    :param changed_files: a string with the list of changed files in a commit (separated by ";").
    :return: True if there is a model file in the list, False otherwise.
    """
    changed_files = changed_files.split(";")
    file_extensions = [get_file_extension(f) for f in changed_files]
    return any([ext in MODEL_FILE_EXTENSIONS for ext in file_extensions])


def is_model_file(file_path: str):
    """
    Check if the file is a model file
    :param file_path: the file path
    :return: True if the file is a model file, False otherwise.
    """
    return get_file_extension(file_path) in MODEL_FILE_EXTENSIONS


def cleanup(folders: list) -> None:
    logger.info("Performing cleanup...")
    # delete the temporary folder
    for folder in folders:
        is_deleted = delete_folder(folder)
        logger.info(f"Deleted folder {folder}? {is_deleted}")


def analyze_slice(df: pd.DataFrame, csv_output: Path, begin: int | None, end: int | None) -> None:
    # load cache
    cache_path = DATA_DIR / "_commit_analysis_cache.sqlite3"
    load_cache(cache_path)

    # create the output dataframes
    output_rows = []
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])
    error_output = csv_output.with_name(csv_output.name.replace("_commits", f"_errors_{begin}-{end}"))
    df_slice = df.iloc[begin:end]

    cache = load_cache_in_memory(cache_path, df_slice)
    logger.info(f"We already have {len(cache)} rows in {cache_path.name}")
    logger.info(f"It will grab the remaining {len(df_slice) - len(cache)} rows")
    # exit(0)
    for _, row in (pbar := tqdm(df_slice.iterrows(), total=len(df_slice), unit="commit")):
        repo_url = row["repo_url"]
        commit_hash = row["commit_hash"]
        pbar.set_postfix_str(f"{repo_url}@{commit_hash}")
        cached_results = cache.get((repo_url,commit_hash)) #get_cached_analysis(cache_path, repo_url, commit_hash)

        if cached_results is not None:
            output_rows.extend(cached_results)
            continue

        repo_clone_path = temp_folder / repo_url.replace("/", "+")

        # if it already exists, remove it, so we can make a new empty one (to avoid clone errors)
        delete_folder(repo_clone_path)
        os.makedirs(repo_clone_path)  # make needed folders

        all_model_files = [f for f in row["all_files_in_tree"].split(";") if is_model_file(f)]
        changed_files = [
            parts[1]
            for item in row["changed_files"].split(";")
            if len(parts := item.split(maxsplit=1)) == 2
        ]

        try:
            commit_results = []
            files_to_download = [x for x in all_model_files if get_file_extension(x) != "safetensors"]
            download_model_files(repo_url, commit_hash, repo_clone_path, files_to_download, logger, timeout=DOWNLOAD_TIMEOUT)

            for model_file in all_model_files:
                extension = get_file_extension(model_file)
                model_file_path = os.path.join(repo_clone_path, model_file)
                # check if it is a symbolic file pointing to nowhere
                if os.path.islink(model_file_path) and not os.path.exists(model_file_path):
                    serialization_format = "UNDETERMINED (symbolic link)"
                else:
                    serialization_format = detect_serialization_format(
                        model_file_path) if extension != "safetensors" else SerializationMethod.SAFETENSORS
                result = {
                    "repo_url": repo_url,
                    "commit_hash": commit_hash,
                    "model_file_path": model_file,
                    "serialization_format": str(serialization_format),
                    "message": row["message"],
                    "author": row["author"],
                    "date": row["date"],
                    "is_in_commit": model_file in changed_files,
                }
                commit_results.append(result)

            save_to_cache(cache_path, repo_url, commit_hash, commit_results)

            output_rows.extend(commit_results)
        except Exception as e:
            logger.error(f"Error processing {commit_hash}: {e}")
            df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": commit_hash, "error": str(e)}


    df_output = pd.DataFrame(output_rows,
        columns=["repo_url", "commit_hash", "model_file_path", "serialization_format", "message", "author", "date", "is_in_commit", ], )

    # after all is said and done, how many unique [repo_url,commit_hash] we have in total?
    logger.info(f"Unique commits: {len(df_output[['repo_url', 'commit_hash']].drop_duplicates())}")

    # save the output dataframes
    df_output.to_csv(csv_output, index=False)
    df_errors.to_csv(error_output, index=False)


def load_commits(commit_file: Path) -> pd.DataFrame:
    if not commit_file.exists():
        logger.info(f"Input file {commit_file} does not exist. Please run `get_commit_logs.py` to generate it.")
        exit(1)

    logger.info(f"Loading the commit history data from {commit_file.name}...")
    df_commits = pd.read_csv(commit_file).fillna("")
    logger.info(f"Total number of commits: {len(df_commits)}")
    # identify the commits that have at least one model file
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    logger.info(f"Number of commits touching at least one model file: {len(df_commits)}")
    return df_commits


if __name__ == '__main__':
    logger.debug(f'Is HF-TRANSFER enabled? {os.environ.get("HF_HUB_ENABLE_HF_TRANSFER", "False")}')

    # create a temporary folder to clone the repositories
    temp_folder = get_tmp_folder()
    temp_folder.mkdir(exist_ok=True)
    logger.info(f"Temp folder: {temp_folder.resolve()}")
    logger.info(f"HF_HUB_CACHE={os.getenv('HF_HUB_CACHE')}")
    # register the cleanup function to be called at the end
    atexit.register(cleanup, [temp_folder])

    # Parse the command line arguments
    args = parse_args()
    group_type = args.group_type
    logger.info(f"Group type: {args.group_type}")
    logger.info(f"Range: {args.begin} - {args.end}")

    # Check if the SSH connection is working
    enforce_ssh(logger)

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / f"selected_{group_type}_commits.csv"
    output_file = DATA_DIR / f"repositories_evolution_{group_type}_commits.csv"
    df_commits = load_commits(input_file)
    analyze_slice(df_commits, output_file, begin=args.begin, end=args.end)

    logger.info(f"Output saved to {output_file.name}")
    logger.info("Done!")
    logger.info("Recommended next steps:")
    logger.info("1. Run the tests on tests/test_analyze_commit_history.py to check the results.")
    logger.info("2. Run the notebooks for the corresponding RQs that use this data.")
