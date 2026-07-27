import unittest
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from scripts.select_models import SAFETENSORS_RELEASE_DATE
from scripts.utils import load
from scripts.select_models import  has_model_file

def fix_data_types(df: DataFrame):
    df['last_modified'] = pd.to_datetime(df['last_modified'], unit='ms', utc=True)
    df['created_at'] = pd.to_datetime(df['created_at'], unit='ms', utc=True)
    df["gated"] = df["gated"].astype(bool)
    return df

class TestSafetensorsReleaseDate(unittest.TestCase):
    def test_safetensors_release_date(self):
        expected_date = pd.to_datetime("2022-09-23")
        self.assertEqual(str(SAFETENSORS_RELEASE_DATE), str(expected_date),
                         f"Expected Safetensors release date to be {expected_date}, but got {SAFETENSORS_RELEASE_DATE}")


class TestSelectModels(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.data_dir = Path("../data")

    def test_selected_models(self):
        num_extra = 10
        df_legacy = fix_data_types(load(self.data_dir / f"selected_legacy_repos.json"))
        df_recent = fix_data_types(load(self.data_dir / f"selected_recent_repos.json"))
        # check that the DataFrame is not empty and has the expected number of models
        self.assertEqual(len(df_legacy) + num_extra, len(df_recent) )
        # check all models are not gated
        self.assertTrue((df_legacy['gated'] == False).all())
        self.assertTrue((df_recent['gated'] == False).all())
        # check that all recent / legacy models are created after / before SAFETENSORS release date
        self.assertTrue((df_recent['created_at'] > SAFETENSORS_RELEASE_DATE).all())
        self.assertTrue((df_legacy['created_at'] <= SAFETENSORS_RELEASE_DATE).all())
        # check that all models have a size greater than 0 and less than 1TB
        self.assertTrue((df_legacy['size'] > 0).all())
        self.assertTrue((df_legacy['size'] < 1 * 1024**4).all())
        self.assertTrue((df_recent['size'] > 0).all())
        self.assertTrue((df_recent['size'] < 1 * 1024**4).all())
        # check that all models have a valid last_modified date
        self.assertTrue((df_legacy['last_modified'] >= pd.to_datetime("2024-01-01", utc=True)).all())
        self.assertTrue((df_recent['last_modified'] >= pd.to_datetime("2024-01-01", utc=True)).all())
        # check that all models  have at least one model file
        self.assertTrue(df_legacy['siblings'].apply(has_model_file).all())
        self.assertTrue(df_recent['siblings'].apply(has_model_file).all())