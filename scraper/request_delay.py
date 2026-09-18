import logging
import random
import time


def wait_random_delay(
    logger: logging.Logger,
    *,
    stage: str,
    min_seconds: float,
    max_seconds: float,
    target: str,
) -> float:
    """アクセス間隔を空け、実際の待機秒数を返す。"""
    if min_seconds < 0 or max_seconds < min_seconds:
        raise ValueError("待機時間は 0 <= min_seconds <= max_seconds で指定してください。")

    delay_seconds = random.uniform(min_seconds, max_seconds)
    logger.info(
        "access_delay stage=%s delay_sec=%.2f target=%s",
        stage,
        delay_seconds,
        target,
    )
    time.sleep(delay_seconds)
    return delay_seconds
