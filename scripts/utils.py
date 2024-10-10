import os
import shutil
import sys

import git
from git import Repo


def delete_folder(folder_location: str) -> bool:
    """
    Delete a folder and its contents.
    :param folder_location: the location of the folder to be deleted.
    :return: True if the folder was deleted (ie, it no longer exist), False otherwise.
    """
    shutil.rmtree(folder_location, ignore_errors=True)

    # check if the folder still exists
    if os.path.exists(folder_location):
        current_os = sys.platform
        if current_os == "Windows": # Use rmdir for Windows
            os.system(f'rmdir /S /Q "{folder_location}"')
        else: # Use rm -rf for Linux/macOS
            os.system(f'rm -rf {folder_location}')
    return not os.path.exists(folder_location)


def clone(repo_url: str, clone_path: str) -> Repo:
    """
    Clone a repository from Hugging Face
    :param repo_url: the repository URL (e.g., "huggingface/transformers")
    :param clone_path: where to clone the repository locally.
    :return: the git repository object.
    """
    clone_url = f"git@hf.co:{repo_url}"
    # Check if the repository directory already exists
    if os.path.exists(clone_path):
        delete_folder(clone_path)
    return git.Repo.clone_from(clone_url, clone_path)
