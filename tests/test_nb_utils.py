import unittest

import pandas as pd

from scripts.notebooks.nb_utils import compute_calendar_week
from scripts.notebooks.nb_utils import SAFETENSORS_RELEASE_DATE

class TestSafetensorsReleaseDate(unittest.TestCase):
    def test_safetensors_release_date(self):
        expected_date = pd.to_datetime("2022-09-22")
        self.assertEqual(str(SAFETENSORS_RELEASE_DATE), str(expected_date),
                         f"Expected Safetensors release date to be {expected_date}, but got {SAFETENSORS_RELEASE_DATE}")




class TestCalendarWeek(unittest.TestCase):
    def vibe_check(self, year, month, day, expected_week):
        date = pd.to_datetime(f"{year}-{month}-{day}")
        actual_week = compute_calendar_week(date)
        self.assertEqual(expected_week, actual_week,
                         f"Expected week {expected_week} for {date}, but got {actual_week}")

    def test_2021(self):
        for day in range(1, 3):
            self.vibe_check(2021, 1, day, 0)
        for day in range(3, 10):
            self.vibe_check(2021, 1, day, 1)
        for day in range(26, 32):
            self.vibe_check(2022, 12, day, 52)

    def test_2022(self):
        for day in range(1, 3):
            self.vibe_check(2022, 1, day, 0)
        for day in range(3, 10):
            self.vibe_check(2022, 1, day, 1)
        for day in range(26, 32):
            self.vibe_check(2022, 12, day, 52)

    def test_2023(self):
        for day in range(1, 2):
            self.vibe_check(2023, 1, day, 0)
        for day in range(2, 9):
            self.vibe_check(2023, 1, day, 1)
        for day in range(9, 16):
            self.vibe_check(2023, 1, day, 2)
        for day in range(25, 32):
            self.vibe_check(2023, 12, day, 52)

    def test_2024(self):
        for day in range(1, 8):
            self.vibe_check(2024, 1, day, 0)
        for day in range(8, 15):
            self.vibe_check(2024, 1, day, 1)
        for day in range(15, 22):
            self.vibe_check(2024, 1, day, 2)
        for day in range(30, 32):
            self.vibe_check(2024, 12, day, 52)