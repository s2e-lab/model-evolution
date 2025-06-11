import datetime
import zipfile
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from analyticaml import MODEL_FILE_EXTENSIONS
from matplotlib.font_manager import FontProperties
from tqdm import tqdm

# Create a font property with Noto Emoji and Roboto Condensed fonts
EMOJI_FONT = FontProperties(fname=Path('../../assets/NotoEmoji-Regular.ttf'))
COLOR_EMOJI_FONT = FontProperties(fname=Path('../../assets/NotoColorEmoji-Regular.ttf'))
ROBOTO_CONDENSED_FONT = FontProperties(fname=Path('../../assets/RobotoCondensed-Regular.ttf'))

# Reference date when safetensors was released
SAFETENSORS_RELEASE_DATE = pd.to_datetime("2022-09-22")
# Data and results directories
DATA_DIR = Path('../../data')
RESULTS_DIR = Path('../../results')


def read_repositories_evolution(group: Literal['recent', 'legacy', 'both'] | str) -> pd.DataFrame:
    """
    Read the commits from the repository evolution dataset.
    :return: a data frame
    """
    if group not in ('recent', 'legacy', 'both'):
        raise ValueError(f"Invalid mode: {group}")

    if group == 'both':
        df_recent = read_repositories_evolution('recent')
        df_legacy = read_repositories_evolution('legacy')
        df = pd.concat([df_recent, df_legacy], ignore_index=True)
        return df

    df = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_commits_processed.csv")
    # ensure date is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    # Calculate elapsed days since reference date (safetensors first release)
    df['elapsed_days'] = (df['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    # Add a change_status to data frame
    df_commits = pd.read_csv(DATA_DIR / f"selected_{group}_commits.csv")
    # set "changed_files" and "all_files_in_tree" columns to empty string if it is NaN
    df_commits["changed_files"] = df_commits["changed_files"].fillna("")
    df_commits["all_files_in_tree"] = df_commits["all_files_in_tree"].fillna("")
    changed_files = dict()  # key = repo_url/file_path&&commit_hash; value = status (added, modified, deleted)
    for index, row in tqdm(df_commits.iterrows(), total=len(df_commits), unit="commit"):
        commit_hash = row["commit_hash"]
        repo_url = row["repo_url"]
        if row["changed_files"]:
            for x in row["changed_files"].split(";"):
                status, file_path = x.split(maxsplit=1)
                changed_files[f"{repo_url}/{file_path}&&{commit_hash}"] = status

    # Add the change_status to the data frame for the files that are in the commit
    df["change_status"] = ""
    for index, row in tqdm(df.iterrows(), total=len(df), unit="commit"):
        commit_hash = row["commit_hash"]
        model_file_path = row["model_file_path"]
        if df.at[index, "is_in_commit"]:
            df.at[index, "change_status"] = changed_files[f"{model_file_path}&&{commit_hash}"]

    return df


def filter_by_extension(changed_files: str) -> bool:
    """
    Implement a filter to check if the list of changed files in a commit has model files.
    A model file is a file that has one of the extensions in MODEL_FILE_EXTENSIONS.
    :param changed_files: a string with the list of changed files in a commit (separated by ";").
    :return: True if there is a model file in the list, False otherwise.
    """
    changed_files = changed_files.split(";")
    file_extensions = [Path(f).suffix[1:] for f in changed_files]
    return any([ext in MODEL_FILE_EXTENSIONS for ext in file_extensions])


def get_commit_log_stats(df_repository_evolution: pd.DataFrame,
                         group: Literal['recent', 'legacy', 'both']) -> pd.Series:
    """
    Read the commits logs extracted for the selected repositories and compute some basic stats.
    :return:
    """
    stats = pd.Series()
    stats.name = f"Commit log stats for {group} repositories"
    if group == 'both':
        stats_recent, total_touching_models_recent, total_adding_models_recent = get_commit_log_stats(
            df_repository_evolution, 'recent')
        stats_legacy, total_touching_models_legacy, total_adding_models_legacy = get_commit_log_stats(
            df_repository_evolution, 'legacy')
        total_touching_model_files = total_touching_models_recent + total_touching_models_legacy
        total_adding_model_files = total_adding_models_recent + total_adding_models_legacy
        # assertion that ensures both stats_recent and stats_legacy have the same keys
        assert set(stats_recent.index) == set(
            stats_legacy.index), "Stats for recent and legacy groups should have the same keys."
        # merge the stats for recent and legacy groups
        for key in set(stats_recent.index):
            stats[key] = stats_recent.get(key, 0) + stats_legacy.get(key, 0)
        return stats, total_touching_model_files, total_adding_model_files

    # Load the repositories and set nan columns to empty string
    input_file = DATA_DIR / f"selected_{group}_commits.csv"
    df = pd.read_csv(input_file).fillna("")

    # exclude repos that are not in the evolution data frame
    repo_urls = df_repository_evolution["repo_url"].unique()
    df = df[df["repo_url"].isin(repo_urls)]
    total_commits = len(df)

    # identify the commits that added/modified/deleted at least one model file
    df = df[df["changed_files"].apply(lambda x: filter_by_extension(x))]
    df.reset_index(drop=True, inplace=True)
    total_touching_model_files = len(df)
    total_repos_touching_model_files = df["repo_url"].nunique()
    # compute commits that modify or add model files
    df_added_model_files = df_repository_evolution[df_repository_evolution['change_status'] == '+']
    total_adding_model_files = len(df_added_model_files[['repo_url', 'commit_hash']].drop_duplicates())
    total_repos_adding_model_files = df_added_model_files['repo_url'].nunique()
    # compute commits that do not contain at least one model file in its tree
    num_empty = 0
    for _, row in df.iterrows():
        all_model_files = []
        for f in row["all_files_in_tree"].split(";"):
            if Path(f).suffix[1:] in MODEL_FILE_EXTENSIONS:
                all_model_files.append(f)
        if len(all_model_files) == 0:
            num_empty += 1

    stats.loc["# commits in all logs (total)"] = total_commits
    stats.loc["# commits modifying/adding/deleting at least one serialized model"] = total_touching_model_files
    stats.loc[
        "# repos associated with commits modifying/adding/deleting at least one serialized model"] = total_repos_touching_model_files
    stats.loc["# commits adding at least one serialized model"] = total_adding_model_files
    stats.loc["# repos associated with commits adding at least one serialized model"] = total_repos_adding_model_files
    stats.loc["# commits containing at least one model file in its tree"] = len(df) - num_empty
    stats.loc["# commits not containing at least one model file"] = num_empty
    stats.loc["# repos"] = df["repo_url"].nunique()
    stats.loc["last commit date"] = df["date"].max()

    return stats, total_touching_model_files, total_adding_model_files


def get_safetensors_releases():
    """
    Get the dates of the safetensors releases based on the tags in its repo.
    :return: a dataframe with the dates of the releases in days since the first release and their corresponding labels
    """
    # Dates of the releases in days since the first release and their corresponding labels
    df_releases = pd.read_csv(DATA_DIR / 'safetensors_tags.csv')
    df_releases['date'] = pd.to_datetime(df_releases['date'])
    df_releases['elapsed_days'] = (df_releases['date'] - SAFETENSORS_RELEASE_DATE).dt.days
    # remove rc releases
    df_releases = df_releases[~df_releases['tag'].str.contains('rc')]

    # for releases on the same date, prefer the one that does not start with python-
    df_releases = (df_releases.sort_values(['date', 'tag'], ascending=[True, False])
                   .drop_duplicates('date', keep='first'))

    # remove the "python-" prefix from the tag
    df_releases['tag'] = df_releases['tag'].str.replace('python-', '')

    return df_releases


def unzip(zip_path: str | Path, extract_to: str = '.') -> None:
    """
    Unzip a zip file to a specified directory.
    :param zip_path:  location of the zip file to extract
    :param extract_to: where to extract the files
    :return: None
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def compute_calendar_week(d: pd.Timestamp) -> int:
    """
    Compute the calendar week for a given date.
    :param d: a pandas Timestamp object representing the date
    :return: the calendar week number (0-52)
    """
    jan1st = datetime.date(d.year, 1, 1)
    dec31st = datetime.date(d.year, 12, 31)
    if jan1st.isocalendar().week > 50:
        # If January 1st is in the last week of the previous year, return week 0
        if d.month == 1 and d.isocalendar().week > 50:
            return 0
        else:
            return d.isocalendar().week

    if dec31st.isocalendar().week == 1:
        # If December 31st is in the first week of the next year, return week 52
        if d.month == 12 and d.isocalendar().week == 1:
            return 52
    # Return the week number, adjusted to start from 0
    return d.isocalendar().week - 1


def compute_calendar_mask(year_matrix: np.ndarray, year: int) -> np.ndarray:
    """
    Compute a mask for a year matrix to indicate which days are valid based on the calendar year.
    :param year_matrix: a 2D numpy array representing the year matrix (7 rows for days, 53 columns for weeks)
    :param year: the year for which to compute the mask
    :return: a boolean mask indicating valid days in the year matrix
    """
    # 1. Determine Jan 1 and Dec 31
    jan1 = datetime.date(year, 1, 1)
    dec31 = datetime.date(year, 12, 31)

    # 2. Compute weekday indexes (0 = Monday, ..., 6 = Sunday)
    jan1_weekday, dec31_weekday = jan1.weekday(), dec31.weekday()

    # 3. Create full False mask
    mask = np.full_like(year_matrix, False, dtype=bool)

    # 4. Mask leading days before Jan 1 in the first week
    mask[:jan1_weekday, 0] = True

    # 5. Mask trailing days after Dec 31 in the last week
    mask[dec31_weekday + 1:, -1] = True if dec31_weekday < 6 else False

    return mask


def compute_year_range(year: int) -> pd.DatetimeIndex:
    """
    Compute a range of dates for the heatmap (what date it should start and when it ends)
    :param year: the year for which to compute the range
    :return: a tuple
    """
    # 1. Determine Jan 1 and Dec 31
    jan1 = datetime.date(year, 1, 1)
    dec31 = datetime.date(year, 12, 31)

    # 2. Compute weekday indexes (0 = Monday, ..., 6 = Sunday)
    jan1_weekday, dec31_weekday = jan1.weekday(), dec31.weekday()

    # compute the subtraction between jan1  and the number of weekday in jan1_weekday
    start_date = jan1 - datetime.timedelta(days=jan1_weekday)
    # compute the addition between dec31 and the number of days until the end of the week
    end_date = dec31 + datetime.timedelta(days=(6 - dec31_weekday))

    return pd.date_range(start=start_date, end=end_date, freq='D')


def get_commit_counts_by_date(df: pd.DataFrame) -> pd.Series:
    """
    Get the number of commits by date.
    :param df: a data frame with a 'date' column that contains commit dates.
    :return: a series with the number of commits by date
    """
    # group by timestamp, and ignore the times, just group based on the date
    commits_by_date = df.groupby(df['date'].dt.floor('D')).size().sort_index()
    # add all dates from SAFE TENSORS RELEASE DATE to today
    for i in range(0, (pd.Timestamp.today() - SAFETENSORS_RELEASE_DATE).days):
        date = SAFETENSORS_RELEASE_DATE + pd.Timedelta(days=i)
        if date not in commits_by_date.index:
            commits_by_date.loc[date] = 0
    commits_by_date = commits_by_date.sort_index()
    commits_by_date.name = 'count'  # name the totals as 'count'
    # Ensure 'files_modified_by_date' has datetime as the index if not already
    commits_by_date.index = pd.to_datetime(commits_by_date.index)
    # Determine the maximum value across the entire dataset to set a common color range
    vmax = commits_by_date.max()
    # Apply a log transformation to the commits, offsetting by 1 to handle zero values
    log_commits_by_date = np.log1p(commits_by_date)  # log(1 + count)
    # Determine the max log-transformed value for setting the consistent color range
    vmax_log = log_commits_by_date.max()
    return commits_by_date, log_commits_by_date, vmax, vmax_log


def extract_metadata(group: str) -> dict:
    """
    Extract metadata from the repository URLs.
    :param repo_urls: a list of repository URLs
    :return: a DataFrame with the extracted metadata
    """
    # Extracted results, load to frame and delete the large CSV
    df_metadata = pd.read_json(DATA_DIR / f"selected_{group}_repos.json")
    # Convert the 'created_at' column to datetime
    df_metadata['created_at'] = pd.to_datetime(df_metadata['created_at'], utc=True)
    df_metadata['last_modified'] = pd.to_datetime(df_metadata['last_modified']/ 1000, unit='s', utc=True)
    df_metadata['lastModified'] = pd.to_datetime(df_metadata['created_at'], utc=True)
    # rename id to 'repo_url' for consistency
    df_metadata.rename(columns={'id': 'repo_url'}, inplace=True)
    # Create a dictionary to map the 'repo_url' to the metadata
    return df_metadata.set_index('repo_url').to_dict(orient='index')


if __name__ == "__main__":
    # mask = compute_calendar_mask(np.zeros((7, 53)), 2023)
    # print(mask)
    # assert compute_calendar_week(pd.Timestamp("2023-01-01")) == 0
    # assert compute_calendar_week(pd.Timestamp("2023-01-01")) == 0
    # d = pd.Timestamp("2022-01-01")
    # print(d, "week=", compute_calendar_week(d))
    #
    # for year in [2022, 2023, 2024]:
    #     r = compute_year_range(year)
    #     print(year, r[0], r[-1])

    all = extract_metadata('recent')

    print(all['speechbrain/ssl-wav2vec2-base-librispeech']['last_modified'])
    print(all['speechbrain/ssl-wav2vec2-base-librispeech']['created_at'])
    print(all['speechbrain/ssl-wav2vec2-base-librispeech']['lastModified'])
