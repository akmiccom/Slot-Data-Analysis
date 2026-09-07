import unittest
from unittest.mock import Mock, patch

from scraper.request_delay import wait_random_delay


class WaitRandomDelayTest(unittest.TestCase):
    @patch("scraper.request_delay.time.sleep")
    @patch("scraper.request_delay.random.uniform", return_value=4.25)
    def test_waits_for_random_duration_and_logs_it(
        self,
        uniform_mock: Mock,
        sleep_mock: Mock,
    ) -> None:
        logger = Mock()

        delay = wait_random_delay(
            logger,
            stage="between_halls",
            min_seconds=3,
            max_seconds=8,
            target="test-hall",
        )

        self.assertEqual(4.25, delay)
        uniform_mock.assert_called_once_with(3, 8)
        sleep_mock.assert_called_once_with(4.25)
        logger.info.assert_called_once_with(
            "access_delay stage=%s delay_sec=%.2f target=%s",
            "between_halls",
            4.25,
            "test-hall",
        )

    def test_rejects_invalid_range(self) -> None:
        with self.assertRaises(ValueError):
            wait_random_delay(
                Mock(),
                stage="test",
                min_seconds=3,
                max_seconds=1,
                target="target",
            )


if __name__ == "__main__":
    unittest.main()
