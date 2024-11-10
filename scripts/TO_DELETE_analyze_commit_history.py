import atexit
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection
from analyticaml.model_parser import detect_serialization_format
from numpy import ndarray, dtype
from pandas import Series
from tqdm import tqdm

import utils


def filter_by_extension(changed_files: str):
    """
    Implement a filter to check if the list of changed files in a commit has model files.
    A model file is a file that has one of the extensions in MODEL_FILE_EXTENSIONS.
    :param changed_files: a string with the list of changed files in a commit (separated by ";").
    :return: True if there is a model file in the list, False otherwise.
    """
    changed_files = changed_files.split(";")
    file_extensions = [Path(f).suffix[1:] for f in changed_files]
    return any([ext in MODEL_FILE_EXTENSIONS for ext in file_extensions])


def is_model_file(file_path: str):
    """
    Check if the file is a model file
    :param file_path: the file path
    :return: True if the file is a model file, False otherwise.
    """
    return Path(file_path).suffix[1:] in MODEL_FILE_EXTENSIONS


def parse_args(max_commits: int):
    """
    Parse the command line arguments
    :return: the start index and end index
    """
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
        if end_idx >= max_commits:
            print(f"The maximum number of commits is {max_commits - 1}. End index must be smaller than that.")
            sys.exit(1)
        if start_idx > end_idx:
            print("The start index must be smaller than the end index")
            sys.exit(1)
        if start_idx < 0:
            print("The start index must be greater than or equal to 0")
            sys.exit(1)

    else:
        print(f"Usage: python {os.path.basename(__file__)} <start_index> <end_index>")
        print("Example: python analyze_snapshots.py 0 100")
        print("This will analyze the commits from index 0 to 100 (inclusive in both ends)")
        print(f"Note: The maximum end index  is {max_commits - 1}")
        sys.exit(1)
    return start_idx, end_idx


def cleanup():
    print("Performing cleanup...")
    # delete the temporary folder
    utils.delete_folder(temp_folder)


def load_cache(filepath: str | Path) -> dict:
    df_commits = pd.read_csv(filepath).fillna("")
    cache = dict()  # key = repo_url + commit_hash + model_file_path -> serialization_format
    # iterate over dataframe to create cache
    for index, row in df_commits.iterrows():
        model_file_path = row['model_file_path'].replace(row['repo_url'] + "/", "")
        key = (row['repo_url'], row['commit_hash'], model_file_path)
        cache[key] = row['serialization_format']
    return cache


def is_all_in_cache(cache: dict, row: pd.Series, all_model_files) -> bool:
    for f in all_model_files:
        if (row['repo_url'], row['commit_hash'], f) not in cache:
            return False
    return True


def get_from_cache(cache: dict, row: pd.Series, file_path: str, changed_files: dict) -> dict:
    key = (row['repo_url'], row['commit_hash'], file_path)
    return {
        "repo_url": row["repo_url"],
        "commit_hash": row["commit_hash"],
        "model_file_path": file_path,
        "serialization_format": cache[key],
        "message": row["message"],
        "author": row["author"],
        "date": row["date"],
        "is_in_commit": file_path in changed_files,
        "change_status": changed_files.get(file_path, "")
    }


if __name__ == '__main__':
    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)
    # register the cleanup function to be called at the end
    atexit.register(cleanup)

    # JUST TO RERUN MISSING COMMITS
    # sys.argv = ["", "0", "4888"]
    # sys.argv = ["", "0", "4"]

    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        sys.exit(1)

    # load prior results to create a local cache
    cache_file = Path("../data/cache/repository_evolution_commits_0_4888.csv")
    cache = load_cache(cache_file)

    # Load the repositories and set nan columns to empty string
    input_file = Path("../data/huggingface_sort_by_createdAt_top996939_commits_0_1035.csv")
    df_commits = pd.read_csv(input_file).fillna("")
    print("Total number of commits:", len(df_commits))

    # identify the commits that have at least one model file
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    print("Number of commits touching at least one model file:", len(df_commits))

    # Parse the command line arguments
    start_idx, end_idx = parse_args(len(df_commits))

    # this is the last repository URL and object, used to avoid cloning the same repository multiple times
    last_repo_url, last_repo_obj, last_clone_path = None, None, None

    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format",
                                      "message", "author", "date", "is_in_commit", "change_status"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])
    # get batch from repos starting at start_idx and ending at end_idx (inclusive)
    batch = df_commits[start_idx:end_idx + 1]

    print(f"Starting batch processing (range = {start_idx}-{end_idx})...")
    # Analysis configuration
    save_at, n, out_suffix = 100, 0, "NEW_repositories_evolution_commits"

    # iterate over the range of commits
    for index, row in tqdm(batch.iterrows(), total=len(batch), unit="commit"):
        # check whether all files are in cache
        all_model_files = [f for f in row["all_files_in_tree"].split(";") if is_model_file(f)]
        changed_files = dict() # key = file_path, value = status (added, modified, deleted)
        for x in row["changed_files"].split(";"):
            status, file_path = x.split(maxsplit=1)
            changed_files[file_path] = status
        all_in_cache = is_all_in_cache(cache, row, all_model_files)
        # if in cache, pull metadata from cache
        if all_in_cache:
            n += 1
            rows = [get_from_cache(cache, row, f, changed_files) for f in all_model_files]
            df_output = pd.concat([df_output, pd.DataFrame(rows)], ignore_index=True)
        else:
            try:
                # checkout repository at that commit hash
                commit_hash = row["commit_hash"]
                repo_url = row["repo_url"]
                clone_path = temp_folder / repo_url.replace("/", "+")

                if last_repo_url != repo_url:
                    # close the last repository and delete the folder
                    if last_repo_obj:
                        last_repo_obj.close()
                        utils.delete_folder(last_clone_path)
                    # clone the repository
                    repo = utils.clone(repo_url, clone_path, single_branch=True, no_tags=True)
                    # update the last repository URL and object
                    last_repo_url, last_repo_obj, last_clone_path = repo_url, repo, clone_path

                # checkout the commit hash
                last_repo_obj.git.checkout(commit_hash, force=True)

                # iterate over the files touched in the commit (modified, added, or deleted)
                for file_path in all_model_files:
                    full_file_path = os.path.join(clone_path, file_path)
                    # check if it is a symbolic file pointing to nowhere
                    if os.path.islink(full_file_path) and not os.path.exists(full_file_path):
                        serialization_format = "UNDETERMINED (symbolic link)"
                    else:
                        serialization_format = detect_serialization_format(full_file_path)
                    # add to df_output
                    df_output.loc[len(df_output)] = {
                        "repo_url": repo_url,
                        "commit_hash": commit_hash,
                        "model_file_path": os.path.join(repo_url, file_path),
                        "serialization_format": serialization_format,
                        "message": row["message"],
                        "author": row["author"],
                        "date": row["date"],
                        "is_in_commit": file_path in changed_files,
                        "change_status": changed_files.get(file_path, "")
                    }
                    # print(f"File: {file_path}, Format: {serialization_format}")
            except Exception as e:
                print(f"Error processing {commit_hash}: {e}")
                df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": commit_hash, "error": e}

        # SAVES THE DATAFRAME EVERY save_at ITERATIONS
        if index != 0 and index % save_at == 0:
            output_file = f"{out_suffix}_{start_idx}_{end_idx}.csv"
            df_output.to_csv(Path("../data") / output_file, index=False)
            df_errors.to_csv(Path("../data") / output_file.replace("commits", "errors"), index=False)

    print(f"How many in cache? {n} commits.")

    # after all is said and done, how many unique [repo_url,commit_hash] we have in total?
    print(f"Unique commits: {len(df_output[['repo_url', 'commit_hash']].drop_duplicates())}")


    # save the output dataframes
    output_file = f"{out_suffix}_{start_idx}_{end_idx}.csv"
    df_output.to_csv(Path("../data") / output_file, index=False)
    df_errors.to_csv(Path("../data") / output_file.replace("commits", "errors"), index=False)

    print(f"Output saved to ../data/{output_file}")
