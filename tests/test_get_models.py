import unittest

from pathlib import Path
from scripts.utils import load

class TestGetModels(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.data_dir = Path("../data")

    def test_get_models(self):
        num_models = 1209409
        df = load(self.data_dir / f"hf_sort_by_createdAt_top{num_models}.json.zip")
        # check that the DataFrame is not empty and has the expected number of models
        self.assertEqual(len(df), num_models, f"Expected {num_models} models, but got {len(df)}")
        # check that all models are created on or before 2024
        self.assertTrue((df['created_at'] <= '2024-12-31').all(), "Not all models are created on or before 2024")
