import os
import time

import psycopg

from config import config
from utils.logger_setup import setup_logger

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def refresh_materialized_views(_supabase=None) -> bool:
    """全データ登録後にダッシュボード用MVを1回だけ更新する。

    長時間処理をSupabase REST/RPC経由で待たないため、Postgresへ直接接続して
    public.refresh_dashboard_materialized_views() を呼び出す。

    SUPABASE_DB_URL が未設定の場合は、ローカル実行などを想定して
    警告を出してMV更新だけをスキップする。

    Returns:
        True: この実行でMV更新を行った
        False: DB URL未設定、または別の更新が実行中でスキップした
    """
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        logger.warning(
            "SUPABASE_DB_URL が未設定のためマテビュー更新をスキップします。"
            "results への登録結果はそのまま保持されます。"
        )
        return False

    start = time.perf_counter()
    logger.info("マテビュー更新開始")

    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("select public.refresh_dashboard_materialized_views();")
                row = cur.fetchone()
    except Exception:
        logger.exception("マテビュー更新失敗")
        raise

    refreshed = bool(row and row[0])
    duration = time.perf_counter() - start

    if refreshed:
        logger.info("マテビュー更新完了: duration_sec=%.2f", duration)
    else:
        logger.warning(
            "別のマテビュー更新が実行中のためスキップ: duration_sec=%.2f",
            duration,
        )

    return refreshed
