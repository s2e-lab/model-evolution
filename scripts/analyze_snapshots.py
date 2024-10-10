import os
import sys
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS
from analyticaml.model_parser import detect_serialization_format
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


def parse_args(max_commits: int):
    """
    Parse the command line arguments
    :return: the start index and end index
    """
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
    else:
        print("Usage: python analyze_snapshots.py <start_index> <end_index>")
        print("Example: python analyze_snapshots.py 0 100")
        print("This will analyze the commits from index 0 to 100 (inclusive in both ends)")
        print(f"Note: The maximum number of commits is {max_commits}")
        sys.exit(1)
    return start_idx, end_idx


if __name__ == '__main__':
    # JUST TO DEBUG
    # sys.argv = ["analyze_snapshots.py", "2926", "2928"]
    # small repo that is easier to test: "savasy/bert-base-turkish-squad"

    # Load the repositories and set nan columns to empty string
    input_file = Path("../data/huggingface_sort_by_createdAt_top996939_commits_0_1035.csv")
    repos = pd.read_csv(input_file).fillna("")

    # identify the commits that have model files
    repos = repos[repos["changed_files"].apply(lambda x: filter_by_extension(x))]
    repos.reset_index(drop=True, inplace=True)

    print(f"Found {len(repos)} commits with model files")

    # Parse the command line arguments
    start_idx, end_idx = parse_args(len(repos))

    # this is the last repository URL and object, used to avoid cloning the same repository multiple times
    last_repo_url, last_repo_obj = None, None

    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)

    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])

    # iterate over the commits
    for index, row in tqdm(repos.iterrows(), total=len(repos)):
        # ignore the commits that are not in the range
        if index < start_idx: continue
        if index > end_idx: break
        # print(index)
        try:
            # checkout repository at that commit hash
            hash = row["commit_hash"]
            repo_url = row["repo_url"]

            clone_path = temp_folder / repo_url.replace("/", "+")

            if last_repo_url != repo_url:
                # close the last repository and delete the folder
                if last_repo_obj is not None:
                    last_repo_obj.close()
                    utils.delete_folder(clone_path)
                # clone the repository
                repo = utils.clone(repo_url, clone_path)
                # update the last repository URL and object
                last_repo_url, last_repo_obj = repo_url, repo

            # checkout the commit hash
            last_repo_obj.git.checkout(hash)

            # now identify the model files and its format
            changed_files = row["changed_files"].split(";")
            for file in changed_files:
                if not filter_by_extension(file):
                    continue
                file_path = os.path.join(clone_path, file)
                serialization_format = detect_serialization_format(file_path)
                # add to df_output
                df_output.loc[len(df_output)] = {
                    "repo_url": repo_url,
                    "commit_hash": hash,
                    "model_file_path": file,
                    "serialization_format": serialization_format}
                print(f"File: {file}, Format: {serialization_format}")
        except Exception as e:
            print(f"Error processing {hash}: {e}")
            df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": hash, "error": e}

    # delete the temporary folder
    utils.delete_folder(temp_folder)

    # save the output dataframes
    output_file = f"repository_evolution_{start_idx}_{end_idx}.csv"
    df_output.to_csv(Path("../results") / output_file, index=False)
    df_errors.to_csv(Path("../results") / output_file.replace(".csv", "_errors.csv"), index=False)
