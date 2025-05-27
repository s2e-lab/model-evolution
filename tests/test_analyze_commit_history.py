import unittest
from pathlib import Path
from unittest.mock import patch

class TestAnalyzeCommitHistory(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.data_dir = Path("../data")

    def test_parse_args(self):
        # Test the parse_args function
        from scripts.analyze_commit_history import parse_args
        args = parse_args()
        self.assertIn(args.group_type, ["legacy", "recent"], "group_type should be either 'legacy' or 'recent'")