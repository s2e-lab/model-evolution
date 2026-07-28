import unittest
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from scripts.utils import load
from test_filter_models import fix_data_types


class TestModelsCommits(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.data_dir = Path("../data")

    def run_assertions(self, df_commits: DataFrame, df_errors:DataFrame, df_repos: DataFrame):
        # check the number of unique repos in each frame is the same
        missing =  set(df_repos["id"]) - (set(df_commits["repo_url"]) | set(df_errors["repo_url"]))
        self.assertEqual(len(missing), 0, f"Missing repositories: {missing}")
        # check that errors are empty
        # self.assertTrue(df_errors.empty)

    def test_get_commit_logs(self):
        for group in ["legacy", "recent"]:
            print(f"Testing get_commit_logs for group {group}")
            df_repos = fix_data_types(load(self.data_dir / f"selected_{group}_repos.json"))
            df_commits = pd.read_csv(self.data_dir / f"selected_{group}_commits.csv")
            df_errors = pd.read_csv(self.data_dir / f"selected_{group}_errors.csv")
            self.run_assertions(df_commits, df_errors, df_repos)