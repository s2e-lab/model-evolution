import atexit
import os
import sys
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection
from analyticaml.model_parser import detect_serialization_format
from huggingface_hub import snapshot_download
from tqdm import tqdm
from utils import delete_folder
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
        print(f"Usage: python {os.path.basename(__file__)} <start_index> <end_index>")
        print("Example: python analyze_snapshots.py 0 100")
        print("This will analyze the commits from index 0 to 100 (inclusive in both ends)")
        print(f"Note: The maximum end index  is {max_commits - 1}")
        sys.exit(1)
    return start_idx, end_idx


def is_deleted_file(commit_file_obj: dict, full_file_path: str | Path):
    """
    Check if the file is deleted
    :param file_path: the file path
    :return: True if the file is deleted, False otherwise
    """
    return not os.path.exists(full_file_path) and commit_file_obj["deletions"] == commit_file_obj["lines"]


def cleanup():
    print("Performing cleanup...")
    # delete the temporary folder
    utils.delete_folder(temp_folder)


if __name__ == '__main__':
    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)

    atexit.register(cleanup)

    # JUST TO RERUN MISSING COMMITS
    sys.argv = ["", "1",  "2"]
    # sys.argv = ["analyze_snapshots.py", "0",  "2999"]
    # sys.argv = ["analyze_snapshots.py", "3000", "4999"]
    # sys.argv = ["analyze_snapshots.py", "5000", "5014"]
    # sys.argv = ["analyze_snapshots.py", "0", "5014"]


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

    # identify the commits that have at least one model file
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    print("Number of commits touching at least one model file:", len(df_commits))

    # Parse the command line arguments
    start_idx, end_idx = parse_args(len(df_commits))

    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format", "message", "author", "date"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])
    # get batch from repos starting at start_idx and ending at end_idx (inclusive)
    batch = df_commits[start_idx:end_idx + 1]

    print(f"Starting batch processing (range = {start_idx}-{end_idx})...")
    save_at = 100
    # iterate over the range of commits
    for index, row in tqdm(batch.iterrows(), total=len(batch), unit="commit"):
        repo_files = row["all_files_in_tree"].split(";")
        model_files = [f for f in repo_files if is_model_file(f)]
        repo_url = row["repo_url"]
        clone_path = temp_folder / repo_url.replace("/", "+")
        commit_hash = row["commit_hash"]
        snapshot_download(repo_id=repo_url,allow_patterns=[f"*.{x}" for x in MODEL_FILE_EXTENSIONS],
                          local_dir=clone_path, revision=commit_hash, force_download=True)
        for file_path in model_files:
            try:
                full_file_path = os.path.join(clone_path, file_path)
                # check if it is a symbolic file pointing to nowhere
                if os.path.islink(full_file_path) and not os.path.exists(full_file_path):
                    serialization_format = "undetermined (symbolic link)"
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
                    "date": row["date"]
                }
            except Exception as e:
                print(f"Error processing {commit_hash}: {e}")
                df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": commit_hash, "error": e}
            finally:
                if os.path.exists(clone_path):
                    delete_folder(clone_path)

        # SAVES THE DATAFRAME EVERY save_at ITERATIONS
        if index != 0 and index % save_at == 0:
            output_file = f"fixed2_repository_evolution_commits_{start_idx}_{end_idx}.csv"
            df_output.to_csv(Path("../data") / output_file, index=False)
            df_errors.to_csv(Path("../data") / output_file.replace("commits", "errors.csv"), index=False)


    # save the output dataframes
    output_file = f"fixed2_repository_evolution_commits_{start_idx}_{end_idx}.csv"
    df_output.to_csv(Path("../data") / output_file, index=False)
    df_errors.to_csv(Path("../data") / output_file.replace("commits", "errors"), index=False)

    print(f"Output saved to ../data/{output_file}")
