import os
import unittest
from unittest.mock import patch

from scraper.run_monitor import (
    ConsecutiveErrorCircuitBreaker,
    build_quality_issues,
    emit_github_annotation,
    positive_int_env,
)


class ConsecutiveErrorCircuitBreakerTest(unittest.TestCase):
    def test_opens_after_same_error_reaches_threshold(self) -> None:
        breaker = ConsecutiveErrorCircuitBreaker(threshold=3)

        self.assertEqual((1, False), breaker.record(TimeoutError("same"))[:2])
        self.assertEqual((2, False), breaker.record(TimeoutError("same"))[:2])
        self.assertEqual((3, True), breaker.record(TimeoutError("same"))[:2])

    def test_different_error_and_reset_restart_count(self) -> None:
        breaker = ConsecutiveErrorCircuitBreaker(threshold=2)

        breaker.record(TimeoutError("first"))
        self.assertEqual((1, False), breaker.record(TimeoutError("second"))[:2])
        breaker.reset()
        self.assertEqual((1, False), breaker.record(TimeoutError("second"))[:2])


class PositiveIntEnvTest(unittest.TestCase):
    def test_uses_default_and_accepts_positive_integer(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(5, positive_int_env("LIMIT", 5))
        with patch.dict(os.environ, {"LIMIT": "2"}, clear=True):
            self.assertEqual(2, positive_int_env("LIMIT", 5))

    def test_rejects_invalid_value(self) -> None:
        for value in ("0", "-1", "abc"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"LIMIT": value}, clear=True
            ):
                with self.assertRaises(ValueError):
                    positive_int_env("LIMIT", 5)


class BuildQualityIssuesTest(unittest.TestCase):
    def test_all_existing_data_is_successful(self) -> None:
        self.assertEqual(
            [],
            build_quality_issues(
                hall_count=67,
                target_count=134,
                hall_error_count=0,
                db_error_count=0,
            ),
        )

    def test_zero_targets_and_caught_errors_are_reported(self) -> None:
        issues = build_quality_issues(
            hall_count=67,
            target_count=0,
            hall_error_count=2,
            db_error_count=3,
        )

        self.assertEqual(3, len(issues))
        self.assertIn("対象件数が0", issues[0])
        self.assertIn("2件", issues[1])
        self.assertIn("3件", issues[2])


class GithubAnnotationTest(unittest.TestCase):
    @patch("builtins.print")
    def test_emits_only_inside_github_actions(self, print_mock) -> None:
        with patch.dict(os.environ, {}, clear=True):
            emit_github_annotation("error", "title", "message")
        print_mock.assert_not_called()

        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            emit_github_annotation("error", "title", "message")
        print_mock.assert_called_once_with(
            "::error title=title::message",
            flush=True,
        )


if __name__ == "__main__":
    unittest.main()
