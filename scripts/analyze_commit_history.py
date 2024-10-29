import os
import sys
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection
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
            print(f"The maximum number of commits is {max_commits}. End index must be smaller than that.")
            sys.exit(1)
        if start_idx > end_idx:
            print("The start index must be smaller than the end index")
            sys.exit(1)
        if start_idx < 0:
            print("The start index must be greater than or equal to 0")
            sys.exit(1)

    else:
        print("Usage: python analyze_snapshots.py <start_index> <end_index>")
        print("Example: python analyze_snapshots.py 0 100")
        print("This will analyze the commits from index 0 to 100 (inclusive in both ends)")
        print(f"Note: The maximum number of commits is {max_commits}")
        sys.exit(1)
    return start_idx, end_idx


def is_deleted_file(commit_file_obj: dict, full_file_path: str|Path):
    """
    Check if the file is deleted
    :param file_path: the file path
    :return: True if the file is deleted, False otherwise
    """
    return not os.path.exists(full_file_path) and commit_file_obj["deletions"] == commit_file_obj["lines"]


if __name__ == '__main__':
    # JUST TO DEBUG
    # sys.argv = ["analyze_snapshots.py", "225", "231"]
    # small repo that is easier to test: "savasy/bert-base-turkish-squad"
    # stanfordnlp / stanza - lij
    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        sys.exit(1)

    # Load the repositories and set nan columns to empty string
    input_file = Path("../data/huggingface_sort_by_createdAt_top996939_commits_0_1035.csv")
    df_commits = pd.read_csv(input_file).fillna("")
    print("Total number of commits:", len(df_commits))

    # identify the commits that have model files
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    print("Number of commits touching at least one model file:", len(df_commits))

    # Parse the command line arguments
    start_idx, end_idx = parse_args(len(df_commits))

    # this is the last repository URL and object, used to avoid cloning the same repository multiple times
    last_repo_url, last_repo_obj = None, None

    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)

    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])
    # get batch from repos starting at start_idx and ending at end_idx (inclusive)
    batch = df_commits[start_idx:end_idx + 1]
    # iterate over the range of commits
    for index, row in tqdm(batch.iterrows(), total=len(batch), unit="commit"):
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

            # commit object
            commit = last_repo_obj.commit(hash)

            # iterate over the files touched in the commit (modified, added, or deleted)
            for file_path, commit_file_obj in commit.stats.files.items():
                full_file_path = os.path.join(clone_path, file_path)

                if is_deleted_file(commit_file_obj, full_file_path) or not is_model_file(file_path):
                    continue

                serialization_format = detect_serialization_format(full_file_path)
                # add to df_output
                df_output.loc[len(df_output)] = {
                    "repo_url": repo_url,
                    "commit_hash": hash,
                    "model_file_path": os.path.join(repo_url, file_path),
                    "serialization_format": serialization_format}
                # print(f"File: {file_path}, Format: {serialization_format}")
        except Exception as e:
            print(f"Error processing {hash}: {e}")
            df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": hash, "error": e}

    # delete the temporary folder
    utils.delete_folder(temp_folder)

    # save the output dataframes
    output_file = f"repository_evolution_{start_idx}_{end_idx}.csv"
    df_output.to_csv(Path("../results") / output_file, index=False)
    df_errors.to_csv(Path("../results") / output_file.replace(".csv", "_errors.csv"), index=False)
