import argparse
import atexit
import os
import sys
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection
from analyticaml.model_parser import detect_serialization_format
from tqdm import tqdm

from utils import DATA_DIR, RESULTS_DIR
from utils import delete_folder, clone


def parse_args():
    """
    Parse the command line arguments
    :return: the parsed arguments
    """
    parser = argparse.ArgumentParser(description="Process repository group.")
    # Positional arguments with strict choices
    parser.add_argument(
        "group_type",
        choices=["legacy", "recent"],
        help="Type of repository group to process: 'legacy' or 'recent'."
    )
    return parser.parse_args()


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


def cleanup():
    print("Performing cleanup...")
    # delete the temporary folder
    delete_folder(temp_folder)


if __name__ == '__main__':
    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)
    # register the cleanup function to be called at the end
    atexit.register(cleanup)

    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        sys.exit(1)

    # Parse the command line arguments
    args = parse_args()
    group_type = args.group_type

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / f"hf_sort_by_createdAt_top996939_{group_type}_commits.csv"
    df_commits = pd.read_csv(input_file).fillna("")
    print("Total number of commits:", len(df_commits))

    # identify the commits that have at least one model file
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    print("Number of commits touching at least one model file:", len(df_commits))

    # this is the last repository URL and object, used to avoid cloning the same repository multiple times
    last_repo_url, last_repo_obj, last_clone_path = None, None, None

    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format",
                                      "message", "author", "date", "is_in_commit"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])

    # Analysis configuration
    print(f"Starting batch processing (range = {0}-{len(df_commits)})...")
    save_at, out_filename = 100, f"repositories_evolution_commits_{group_type}.csv"

    # iterate over the range of commits
    for index, row in tqdm(df_commits.iterrows(), total=len(df_commits), unit="commit"):
        all_model_files = [f for f in row["all_files_in_tree"].split(";") if is_model_file(f)]
        changed_files = [x.split()[1] for x in row["changed_files"].split(";")]
        try:
            # checkout repository at that commit hash
            commit_hash = row["commit_hash"]
            repo_url = row["repo_url"]
            clone_path = temp_folder / repo_url.replace("/", "+")

            if last_repo_url != repo_url:
                # close the last repository and delete the folder
                if last_repo_obj:
                    last_repo_obj.close()
                    delete_folder(last_clone_path)
                # clone the repository
                repo = clone(repo_url, clone_path, single_branch=True, no_tags=True)
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
                }
                # print(f"File: {file_path}, Format: {serialization_format}")
        except Exception as e:
            print(f"Error processing {commit_hash}: {e}")
            df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": commit_hash, "error": e}

        # SAVES THE DATAFRAME EVERY save_at ITERATIONS
        if index != 0 and index % save_at == 0:
            df_output.to_csv(DATA_DIR / out_filename, index=False)
            df_errors.to_csv(DATA_DIR / out_filename.replace("commits", "errors"), index=False)

    # after all is said and done, how many unique [repo_url,commit_hash] we have in total?
    print(f"Unique commits: {len(df_output[['repo_url', 'commit_hash']].drop_duplicates())}")

    # save the output dataframes
    df_output.to_csv(DATA_DIR / out_filename, index=False)
    df_errors.to_csv(DATA_DIR / out_filename.replace("commits", "errors"), index=False)

    print(f"Output saved to {DATA_DIR}/{out_filename}")
