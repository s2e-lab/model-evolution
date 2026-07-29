"""
Utility global variables and functions that are used across the project.
@Author:  Joanna C. S. Santos
"""
import errno
import math
import os
import shutil
import stat
import sys
import time
import zipfile
from logging import Logger
from pathlib import Path

import git
import pandas as pd
from datasets import tqdm
from git import Repo
from huggingface_hub import hf_hub_download
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RESULTS_DIR = ROOT_DIR / "results"
SCRIPTS_DIR = ROOT_DIR / "scripts"


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


def clone(repo_url: str, clone_path: str, is_bare: bool = False, no_tags: bool = False, single_branch: bool = False) -> Repo:
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


def calculate_sample_size(population_size: int, confidence_level: float, margin_error: float, proportion: float = 0.5) -> int:
    """
    Calculate the required sample size for a finite population.
    :param population_size: the size of the population.
    :param confidence_level: confidence level (e.g., 0.95 for 95% confidence level).
    :param margin_error: margin of error (e.g., 0.05 for 5% margin of error).
    :param proportion: the proportion of the population that has a certain characteristic (default is 0.5).
    :return: the sample size needed to estimate the population proportion with the desired margin of error and confidence level.
    """
    if population_size <= 0:
        return 0

    # Z-values for the given confidence levels
    z_values = {
        0.90: 1.645,
        0.95: 1.96,
        0.96: 2.05,
        0.97: 2.17,
        0.98: 2.33,
        0.99: 2.576
    }
    confidence_z = z_values[confidence_level]
    numerator = (
            population_size
            * confidence_z ** 2
            * proportion
            * (1 - proportion)
    )

    denominator = (
            margin_error ** 2 * (population_size - 1)
            + confidence_z ** 2 * proportion * (1 - proportion)
    )

    return min(population_size, math.ceil(numerator / denominator))


def calculate_sample_size_OLD(population_size: int,
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


# https://stackoverflow.com/a/1214935 (modified to add os.unlink on the tuple)
def handle_remove_readonly(func, path, exc):
    """
    Handle the removal of read-only files and directories.
    :param func:
    :param path:
    :param exc:
    :return:
    """
    exc_value = exc[1]
    if func in (os.rmdir, os.unlink, os.remove) and exc_value.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
        func(path)
    else:
        raise


def download_model_files(repo: str, sha: str, dir_name: str, model_files: list[str], logger: Logger) -> str:
    """
    Download individual files from a HuggingFace model repository.
    :param repo: HuggingFace model repo ID (e.g., org/repo-name).
    :param sha: Git commit hash or tag.
    :param dir_name: Local directory to download files to.
    :param model_files: List of filenames to download.
    :param logger: Logger instance for logging messages.
    :return: the SHA (passed through unchanged).
    """
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0")
    max_retries, base_delay = 2, 5  # Maximum number of retries and base delay in seconds
    for f in (pbar := tqdm(model_files, unit='file')):
        pbar.set_postfix_str(f)
        for attempt in range(1, max_retries + 1):
            try:
                hf_hub_download(repo_id=repo, filename=f, local_dir=dir_name, revision=sha, user_agent=user_agent)
                break
            except Exception as e:
                logger.debug(f"⚠️ Failed to download {f} (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    wait = base_delay * (2 ** (attempt - 1))
                    logger.debug(f"🔁 Retrying in {wait} seconds...")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"❌ Download failed after {max_retries} attempts for {f}")

    return sha


def get_file_extension(file_path: str) -> str:
    """
    Return the file extension from the file path (full path or just filename).
    :param file_path: the filename/filepath
    :return: the file extension.
    """
    return Path(file_path).suffix.lstrip(".")


def enforce_ssh(logger: Logger | None = None):
    """
    Check if the SSH connection to Hugging Face is working.
    :param logger: Logger instance for logging messages (if set to None, print to stdout).
    """
    from analyticaml import check_ssh_connection

    if check_ssh_connection():
        return

    log = logger.error if logger else print

    log("Please set up your SSH keys on Hugging Face.")
    log("https://huggingface.co/docs/hub/en/security-git-ssh")
    log("Run the following command to check if your SSH connection is working:")
    log("ssh -T git@hf.co")
    log("If it is anonymous, you need to add your SSH key to your Hugging Face account.")
    sys.exit(1)

def get_tmp_folder() -> Path:
    import socket
    if "crc.nd.edu" in socket.gethostname():
        return Path("/groups/jdasilv2/tmp")
    return Path("./tmp")