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

    Returns:
        True: この実行でMV更新を行った
        False: 別の更新が実行中でadvisory lockを取得できなかった
    """
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        raise RuntimeError(
            "SUPABASE_DB_URL が設定されていません。"
            "GitHub Actions Secrets にPostgres接続文字列を設定してください。"
        )

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
