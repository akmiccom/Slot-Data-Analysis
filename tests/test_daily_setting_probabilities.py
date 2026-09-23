import os
import unittest
from unittest.mock import MagicMock, patch

from scraper.daily_setting_probabilities import refresh_daily_setting_probabilities


class RefreshDailySettingProbabilitiesTest(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_skips_when_db_url_is_missing(self):
        self.assertEqual(refresh_daily_setting_probabilities(["2026-09-22"]), 0)

    @patch("scraper.daily_setting_probabilities.psycopg.connect")
    @patch.dict(os.environ, {"SUPABASE_DB_URL": "postgresql://example"}, clear=True)
    def test_refreshes_unique_dates_in_sorted_order(self, connect):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [(12,), (34,)]
        connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor

        refreshed = refresh_daily_setting_probabilities(
            ["2026-09-22", "2026-09-21", "2026-09-22"]
        )

        self.assertEqual(refreshed, 46)
        self.assertEqual(cursor.execute.call_count, 2)
        self.assertEqual(
            cursor.execute.call_args_list[0].args[1],
            ("2026-09-21", "2026-09-21"),
        )
        self.assertEqual(
            cursor.execute.call_args_list[1].args[1],
            ("2026-09-22", "2026-09-22"),
        )


if __name__ == "__main__":
    unittest.main()
