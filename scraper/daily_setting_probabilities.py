import os
import time
from collections.abc import Iterable

import psycopg

from config import config
from utils.logger_setup import setup_logger

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def refresh_daily_setting_probabilities(target_dates: Iterable[str]) -> int:
    """results 更新後に、更新対象日だけ日次設定確率を再計算する。

    public.refresh_daily_setting_probabilities(date, date) をPostgresへ直接接続して
    日付ごとに呼び出す。通常運用では当日分のみ、TARGET_DATES 等で過去日を
    再取得した場合は実際に更新された日付のみ再計算する。

    SUPABASE_DB_URL が未設定の場合は、ローカル実行などを想定して警告を出し、
    設定確率更新だけをスキップする。

    Returns:
        UPSERTされた daily_setting_probabilities の合計行数。
        DB URL未設定、または対象日なしの場合は0。
    """
    dates = sorted({str(target_date) for target_date in target_dates if target_date})
    if not dates:
        logger.info("設定確率更新対象日がないためスキップします。")
        return 0

    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        logger.warning(
            "SUPABASE_DB_URL が未設定のため日次設定確率更新をスキップします。"
            "results への登録結果はそのまま保持されます。"
        )
        return 0

    start = time.perf_counter()
    total_upserted = 0
    logger.info("日次設定確率更新開始: dates=%s", ",".join(dates))

    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                for target_date in dates:
                    cur.execute(
                        "select public.refresh_daily_setting_probabilities(%s::date, %s::date);",
                        (target_date, target_date),
                    )
                    row = cur.fetchone()
                    upserted = int(row[0]) if row and row[0] is not None else 0
                    total_upserted += upserted
                    logger.info(
                        "日次設定確率更新完了: date=%s, rows=%d",
                        target_date,
                        upserted,
                    )
    except Exception:
        logger.exception("日次設定確率更新失敗: dates=%s", ",".join(dates))
        raise

    logger.info(
        "日次設定確率更新完了: dates=%d, rows=%d, duration_sec=%.2f",
        len(dates),
        total_upserted,
        time.perf_counter() - start,
    )
    return total_upserted
