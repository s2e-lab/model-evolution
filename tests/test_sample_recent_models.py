import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sample_recent_models import sample


class TestSampleRecentModels(unittest.TestCase):
    def test_excluded_repositories_count_toward_population_but_are_not_sampled(self):
        df = pd.DataFrame(
            {
                "id": ["previous", "excluded", "new-1", "new-2"],
                "created_at": ["2022-07-01"] * 4,
            }
        )
        output = io.StringIO()

        with redirect_stdout(output):
            sampled = sample(
                df,
                previous_repos={"previous", "excluded"},
                exclude_repos={"excluded"},
            )

        self.assertEqual(set(sampled["id"]), {"previous", "new-1", "new-2"})
        self.assertNotIn("excluded", set(sampled["id"]))
        self.assertIn(
            "2022Q3: population=4, sample=3, reused=1, new=2",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
