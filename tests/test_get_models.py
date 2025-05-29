import unittest

from pathlib import Path

import pandas as pd

from scripts.utils import load

class TestGetModels(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.data_dir = Path("../data")

    def test_get_models(self):
        num_models = 1209240
        df = load(self.data_dir / f"hf_sort_by_createdAt_top{num_models}.json.zip")
        df['last_modified'] = pd.to_datetime(df['last_modified'], utc=True)
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        # check that the DataFrame is not empty and has the expected number of models
        self.assertEqual(len(df), num_models, f"Expected {num_models} models, but got {len(df)}")
        # check that all models are created on or before 2024
        print("Min creation date = ", df["created_at"].min())
        print("Max creation date = ", df["created_at"].max())
        self.assertTrue((df['created_at'] < pd.to_datetime("2025-01-01", utc=True)).all(), "Not all models are created on or before 2024")
