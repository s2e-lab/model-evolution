import math
import os
import shutil
import sys
import zipfile
from pathlib import Path

import git
import pandas as pd
from git import Repo

# DATA_DIR = Path("../data")
DATA_DIR = Path(__file__).parent / "../data"
# RESULTS_DIR = Path("../results")
RESULTS_DIR = Path(__file__).parent / "../results"

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
        if current_os.lower() in ["windows", "win32"]:  # Use rmdir for Windows
            os.system(f'rmdir /S /Q "{folder_location}"')
        else:  # Use rm -rf for Linux/macOS
            os.system(f'rm -rf {folder_location}')
    # if os.path.exists(folder_location):
    #     raise Exception(f"Failed to delete the folder: {folder_location}")
    return not os.path.exists(folder_location)


def clone(repo_url: str, clone_path: str, is_bare: bool = False, no_tags:bool = False, single_branch:bool = False) -> Repo:
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
    return git.Repo.clone_from(clone_url, clone_path, bare=is_bare, no_tags=no_tags, single_branch=single_branch)


def calculate_sample_size(population_size: int,
                          confidence_level: float,
                          margin_of_error: float,
                          proportion: float = 0.5):
    """
    Calculate the sample size for a given population size, confidence level, margin of error, and proportion.
    :param population_size: the size of the population.
    :param confidence_level: confidence level (e.g., 0.95 for 95% confidence level).
    :param margin_of_error: margin of error (e.g., 0.05 for 5% margin of error).
    :param proportion: the proportion of the population that has a certain characteristic (default is 0.5).
    :return: the sample size needed to estimate the population proportion with the desired margin of error and confidence level.
    """
    # Z-values for the given confidence levels
    Z_values = {
        0.90: 1.645,
        0.95: 1.96,
        0.96: 2.05,
        0.97: 2.17,
        0.98: 2.33,
        0.99: 2.576
    }

    Z = Z_values[confidence_level]

    p = proportion
    E = margin_of_error
    N = population_size

    numerator = ((Z ** 2) * p * (1 - p)) / (E ** 2)
    denominator = 1 + (((Z ** 2) * p * (1 - p)) / (E ** 2 * N))

    n = numerator / denominator
    return math.ceil(n)


def load(file_path: Path) -> pd.DataFrame:
    """
    This function loads the data from the Hugging Face API.
    :param file_path: path to the zip file to be loaded.
    :return: a pandas DataFrame with the metadata of the models.
    """
    # check if it is a zip file
    if file_path.suffix == ".zip":
        # uncompress zip file to the DATA_DIR
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
        # load the data
        df = pd.read_json(file_path.with_suffix(""))
        # delete the unzipped file
        os.remove(file_path.with_suffix(""))
    else:
        # load the data directly
        df = pd.read_json(file_path)
    return df
