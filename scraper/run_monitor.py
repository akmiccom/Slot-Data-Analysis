from __future__ import annotations

from dataclasses import dataclass
import os


class RunQualityError(RuntimeError):
    """収集結果が成功として扱えない場合に送出する。"""


class CircuitBreakerOpenError(RunQualityError):
    """同種のタイムアウトが連続し、収集を打ち切った場合に送出する。"""


@dataclass
class ConsecutiveErrorCircuitBreaker:
    threshold: int
    _signature: str | None = None
    _count: int = 0

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold は1以上で指定してください。")

    @staticmethod
    def _error_signature(error: Exception) -> str:
        first_line = str(error).splitlines()[0].strip()
        return f"{type(error).__name__}:{first_line}"

    def record(self, error: Exception) -> tuple[int, bool, str]:
        signature = self._error_signature(error)
        if signature == self._signature:
            self._count += 1
        else:
            self._signature = signature
            self._count = 1
        return self._count, self._count >= self.threshold, signature

    def reset(self) -> None:
        self._signature = None
        self._count = 0


def positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} は1以上の整数で指定してください: {raw_value}") from exc
    if value < 1:
        raise ValueError(f"{name} は1以上の整数で指定してください: {raw_value}")
    return value


def build_quality_issues(
    *,
    hall_count: int,
    target_count: int,
    hall_error_count: int,
    db_error_count: int,
) -> list[str]:
    issues: list[str] = []
    if hall_count and target_count == 0:
        issues.append("有効ホールがあるのに対象件数が0です")
    if hall_error_count:
        issues.append(f"ホール処理エラーが{hall_error_count}件あります")
    if db_error_count:
        issues.append(f"DB登録エラーが{db_error_count}件あります")
    return issues


def emit_github_annotation(level: str, title: str, message: str) -> None:
    """GitHub Actions上でエラー・警告を見つけやすくする。"""
    if os.getenv("GITHUB_ACTIONS", "").lower() != "true":
        return
    if level not in {"error", "warning", "notice"}:
        raise ValueError(f"未対応のannotation levelです: {level}")

    def escape_data(value: str) -> str:
        return (
            value.replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
        )

    def escape_property(value: str) -> str:
        return (
            escape_data(value)
            .replace(":", "%3A")
            .replace(",", "%2C")
        )

    print(
        f"::{level} title={escape_property(title)}::{escape_data(message)}",
        flush=True,
    )
