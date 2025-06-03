import unittest

import pandas as pd

from scripts.analyze_commit_history import filter_by_extension
from scripts.analyze_commit_history import is_model_file
from scripts.utils import DATA_DIR


class TestAnalyzeCommitHistory(unittest.TestCase):

    def debug_differences(df_commits: pd.DataFrame, df_evolution_commits: pd.DataFrame):
        """
        Debugs the differences between two DataFrames containing commit information.
        :param df_evolution_commits:
        :return:
        """
        ## finds missing commits
        missing_commits = df_commits[~df_commits["commit_hash"].isin(df_evolution_commits["commit_hash"])]
        print(missing_commits)

        # finds those that are in df_evolution_commits but not in df_commits
        extra_commits = df_evolution_commits[~df_evolution_commits["commit_hash"].isin(df_commits["commit_hash"])]
        print(extra_commits)
        # finds those that are in df_commits and in df_evolution_commits
        common_commits = df_commits[df_commits["commit_hash"].isin(df_evolution_commits["commit_hash"])]
        print(common_commits)

    def test_commits_completeness(self):
        group = "recent"
        # load up data
        df_commits = pd.read_csv(DATA_DIR / f"selected_{group}_commits.csv").fillna("")
        df_evolution_commits = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_commits.csv")
        df_evolution_errors = pd.read_csv(DATA_DIR / f"repositories_evolution_{group}_errors.csv")
        ## Get repos that failed
        failed_repos = df_evolution_errors["repo_url"].unique()
        ## Identify the commits that have at least one model file
        df_commits = df_commits[df_commits["changed_files"].apply(lambda x: filter_by_extension(x))]
        ## Identify the commits that have at least one model file in all_files_in_tree, which is a semicolon-separated string
        df_commits = df_commits[df_commits["all_files_in_tree"].apply(lambda x: filter_by_extension(x))]
        ## Exclude from df_commits the failed repos
        df_commits = df_commits[~df_commits["repo_url"].isin(failed_repos)]

        ## Check if all commits in df_commits are present in df_evolution_commits
        self.assertTrue(df_commits["commit_hash"].isin(df_evolution_commits["commit_hash"]).all(),
                        "Not all commits in df_commits are present in df_evolution_commits")

    def test_model_files_detection(self):
        # Test with a string of changed files
        changed_files = "model.pkl;script.py;data.csv"
        self.assertTrue(filter_by_extension(changed_files), "filter_by_extension should return True for model files")

        # Test with a single model file
        self.assertTrue(is_model_file("model.pkl"), "is_model_file should return True for model files")

        # Test with a non-model file
        self.assertFalse(is_model_file("script.py"), "is_model_file should return False for non-model files")
