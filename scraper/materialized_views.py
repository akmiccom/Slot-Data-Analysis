import os
import time

import psycopg

from config import config
from utils.logger_setup import setup_logger

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)

MATERIALIZED_VIEWS = (
    "dashboard_active_units_mv",
    "dashboard_active_hall_models_mv",
    "dashboard_results_mv",
    "dashboard_pivot_daily_mv",
    "dashboard_unit_pattern_monthly_mv",
)

ADVISORY_LOCK_KEY = "dashboard_materialized_views_refresh"


def refresh_materialized_views(_supabase=None) -> bool:
    """全データ登録後にダッシュボード用MVを1回だけ更新する。

    Postgresへ直接接続し、セッション単位のadvisory lockで多重実行を防いだ上で、
    各MVを個別SQLとして順番に更新する。1つのSQL関数呼び出しに全MV更新を
    まとめないことで、接続経路側のstatement timeoutが全MVの累積時間に
    適用されることを避ける。

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
                cur.execute(
                    "select pg_try_advisory_lock(hashtextextended(%s, 0));",
                    (ADVISORY_LOCK_KEY,),
                )
                row = cur.fetchone()
                if not row or not row[0]:
                    duration = time.perf_counter() - start
                    logger.warning(
                        "別のマテビュー更新が実行中のためスキップ: duration_sec=%.2f",
                        duration,
                    )
                    return False

                try:
                    for view in MATERIALIZED_VIEWS:
                        view_start = time.perf_counter()
                        logger.info("マテビュー個別更新開始: view=%s", view)
                        cur.execute(
                            f"refresh materialized view concurrently public.{view}"
                        )
                        logger.info(
                            "マテビュー個別更新完了: view=%s, duration_sec=%.2f",
                            view,
                            time.perf_counter() - view_start,
                        )
                finally:
                    cur.execute(
                        "select pg_advisory_unlock(hashtextextended(%s, 0));",
                        (ADVISORY_LOCK_KEY,),
                    )
    except Exception:
        logger.exception("マテビュー更新失敗")
        raise

    duration = time.perf_counter() - start
    logger.info("マテビュー更新完了: duration_sec=%.2f", duration)
    return True
