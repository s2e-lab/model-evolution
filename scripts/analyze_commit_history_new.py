import argparse
import atexit
import os
import sys
from pathlib import Path

import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS, check_ssh_connection
from analyticaml.model_parser import detect_serialization_format
from tqdm import tqdm

from utils import DATA_DIR, RESULTS_DIR, download_model_files, get_file_extension
from utils import delete_folder, clone

# configure logger
import logging
import sys

DEBUG = True
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


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


def analyze_slice(df: pd.DataFrame, csv_output: Path, begin: int | None, end: int | None) -> None:
    # create the output dataframes
    df_output = pd.DataFrame(columns=["repo_url", "commit_hash", "model_file_path", "serialization_format",
                                      "message", "author", "date", "is_in_commit"])
    df_errors = pd.DataFrame(columns=["repo_url", "commit_hash", "error"])
    error_output = csv_output.with_name(csv_output.name.replace("commits", "errors"))
    df_slice = df.iloc[begin:end]
    save_at = 100
    for index, row in tqdm(df_slice.iterrows(), total=len(df_slice), unit="commit"):
        if index != 0 and index % save_at == 0: # saves periodically
            df_output.to_csv(csv_output, index=False)
            df_errors.to_csv(error_output, index=False)

        repo_url = row["repo_url"]
        repo_clone_path = temp_folder / repo_url.replace("/", "+")

        # if it already exists, remove it, so we can make a new empty one (to avoid clone errors)
        delete_folder(repo_clone_path)
        os.makedirs(repo_clone_path)  # make needed folders
        print(f"Downloading model files from {repo_clone_path}")

        commit_hash = row["commit_hash"]
        all_model_files = [f for f in row["all_files_in_tree"].split(";") if is_model_file(f)]
        changed_files = [x.split()[1] for x in row["changed_files"].split(";")]
        # try:
        download_model_files(repo_url, commit_hash, repo_clone_path, [x for x in all_model_files if get_file_extension(x) != "safetensors"], logger)
        for model_file in all_model_files:
            model_file_path = os.path.join(repo_clone_path, model_file["file_path"])
            # check if it is a symbolic file pointing to nowhere
            if os.path.islink(model_file_path) and not os.path.exists(model_file_path):
                serialization_format = "UNDETERMINED (symbolic link)"
            else:
                serialization_format = detect_serialization_format(model_file_path) if model_file[
                                                                                           "extension"] != "safetensors" else SerializationMethod.SAFETENSORS
            df_output.loc[len(df_output)] = {
                "repo_url": repo_url,
                "commit_hash": commit_hash,
                "model_file_path": model_file_path,
                "serialization_format": serialization_format,
                "message": row["message"],
                "author": row["author"],
                "date": row["date"],
                "is_in_commit": model_file["file_path"] in changed_files,
            }
        # except Exception as e:
        #     print(f"Error processing {commit_hash}: {e}")
        #     df_errors.loc[len(df_errors)] = {"repo_url": repo_url, "commit_hash": commit_hash, "error": e}


        # after all is said and done, how many unique [repo_url,commit_hash] we have in total?
        print(f"Unique commits: {len(df_output[['repo_url', 'commit_hash']].drop_duplicates())}")

        # save the output dataframes
        df_output.to_csv(csv_output, index=False)
        df_errors.to_csv(error_output, index=False)


def load_commits(commit_file: Path) -> pd.DataFrame:
    if not commit_file.exists():
        logger.debug(f"Input file {commit_file} does not exist. Please run `get_commit_logs.py` to generate it.")
        exit(1)

    logger.debug(f"Loading the commit history data from {commit_file.name}...")
    df_commits = pd.read_csv(commit_file).fillna("")
    logger.debug(f"Total number of commits: {len(df_commits)}")
    # identify the commits that have at least one model file
    df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
    df_commits.reset_index(drop=True, inplace=True)
    logger.debug(f"Number of commits touching at least one model file: {len(df_commits)}")
    return df_commits


if __name__ == '__main__':
    logger.debug(f'Is HF-TRANSFER enabled? {os.environ.get("HF_HUB_ENABLE_HF_TRANSFER", "False")}')

    # create a temporary folder to clone the repositories
    temp_folder = Path("./tmp")
    temp_folder.mkdir(exist_ok=True)
    # register the cleanup function to be called at the end
    atexit.register(cleanup)

    # Parse the command line arguments
    args = parse_args()
    group_type = args.group_type

    # Check if the SSH connection is working
    if not check_ssh_connection():
        print("Please set up your SSH keys on HuggingFace.")
        print("https://huggingface.co/docs/hub/en/security-git-ssh")
        print("Run the following command to check if your SSH connection is working:")
        print("ssh -T git@hf.co")
        print("If it is anonymous, you need to add your SSH key to your HuggingFace account.")
        exit(1)

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / f"selected_{group_type}_commits.csv"
    output_file = DATA_DIR / f"repositories_evolution_{group_type}_commits.csv"
    df_commits = load_commits(input_file)
    analyze_slice(df_commits, output_file, begin=args.begin, end=args.end)

    print(f"Output saved to {output_file.name}")
    print("Done!")
    print("Recommended next steps:")
    print("1. Run the tests on tests/test_analyze_commit_history.py to check the results.")
    print("1. Run the hotfix to discard extra repos from the recent group, to balance out the sizes on each category.")
    print("2. Run the notebooks for the corresponding RQs that use this data.")
