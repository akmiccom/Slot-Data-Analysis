import pandas as pd
from urllib.parse import quote, urljoin
import os
import datetime as dt
import re
import time
import yaml
from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

from config import config
from utils.logger_setup import setup_logger
from scraper.scraping_result_data import RESULT_COLUMNS, extract_result_data_by_dates
from scraper.preprocess_for_db import df_data_clean
from scraper import data_to_supabase
from scraper.materialized_views import refresh_materialized_views
from scraper.run_monitor import (
    CircuitBreakerOpenError,
    ConsecutiveErrorCircuitBreaker,
    RunQualityError,
    build_quality_issues,
    emit_github_annotation,
    positive_int_env,
)
from scraper.supabase_lookup import has_enough_results

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def _parse_bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() == "true"


def _load_target_dates_from_env() -> set[str] | None:
    raw_target_dates = os.getenv("TARGET_DATES", "").strip()
    if not raw_target_dates:
        return None

    target_dates: set[str] = set()
    for raw_date in raw_target_dates.split(","):
        target_date = raw_date.strip()
        if not target_date:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", target_date):
            raise ValueError(f"TARGET_DATES は YYYY-MM-DD のカンマ区切りで指定してください: {target_date}")
        try:
            dt.date.fromisoformat(target_date)
        except ValueError as exc:
            raise ValueError(f"TARGET_DATES は YYYY-MM-DD のカンマ区切りで指定してください: {target_date}") from exc
        target_dates.add(target_date)

    if not target_dates:
        raise ValueError("TARGET_DATES に有効な日付が指定されていません。")

    logger.info("手動指定日付: target_dates=%s", ",".join(sorted(target_dates)))
    return target_dates


# =========================
# ページ操作
# =========================
def _load_hall_list(test_mode: bool = False, test_count: int = 2) -> list[config.HallInfo]:
    if not os.path.exists(config.HALLS_YAML):
        raise FileNotFoundError(f"YAMLが見つかりません: {config.HALLS_YAML}")
    with open(config.HALLS_YAML, "r", encoding="utf-8") as f:
        halls_cfg = yaml.safe_load(f).get("halls", [])

    all_halls: list[config.HallInfo] = [
        config.HallInfo(
            name=h.get("name", h.get("slug", "")),
            prefecture=h.get("prefecture", ""),
            slug=h["slug"],
            enabled=h.get("enabled", True),
            period=int(h["period"]),
        )
        for h in halls_cfg
    ]
    disabled_count = sum(not h.enabled for h in all_halls)
    hall_list = [h for h in all_halls if h.enabled]

    enabled_count = len(hall_list)
    if test_mode:
        hall_list = hall_list[:test_count]
        logger.info("*********** テストモードで実行しています。 **********")

    logger.info(
        "ホール設定読み込み: enabled_halls=%d, processing_halls=%d, disabled_halls=%d",
        enabled_count,
        len(hall_list),
        disabled_count,
    )
    return hall_list


def _upsert_hall_date(
    df_hall_date: pd.DataFrame,
    supabase,
    *,
    hall: str,
    date: str,
) -> int:
    db_start = time.perf_counter()
    if df_hall_date.empty:
        logger.warning("空データのためDB登録をスキップします。")
        return 0

    preprocess_start = time.perf_counter()
    df_clean = df_data_clean(df_hall_date)
    logger.info(
        "timing stage=db_preprocess hall=%s date=%s rows=%d duration_sec=%.2f",
        hall,
        date,
        len(df_hall_date),
        time.perf_counter() - preprocess_start,
    )
    if df_clean.empty:
        logger.warning("前処理後のデータが空のためDB登録をスキップします。")
        return 0

    dimension_start = time.perf_counter()
    data_to_supabase.add_model(df_clean, supabase)
    data_to_supabase.add_prefecture_and_hall(df_clean, supabase)
    logger.info(
        "timing stage=db_dimensions hall=%s date=%s rows=%d duration_sec=%.2f",
        hall,
        date,
        len(df_clean),
        time.perf_counter() - dimension_start,
    )

    result_start = time.perf_counter()
    upserted_rows = data_to_supabase.add_data_result(df_clean, supabase)
    logger.info(
        "timing stage=db_results hall=%s date=%s rows=%d duration_sec=%.2f",
        hall,
        date,
        upserted_rows,
        time.perf_counter() - result_start,
    )
    logger.info(
        "timing stage=db_total hall=%s date=%s rows=%d duration_sec=%.2f",
        hall,
        date,
        upserted_rows,
        time.perf_counter() - db_start,
    )
    return upserted_rows


def scraper_all_hall(
    test_mode: bool = False,
    test_count: int = 2,
    min_existing_rows: int = 10,
    upsert_each_date: bool = True,
) -> pd.DataFrame:
    start = time.perf_counter()
    load_halls_start = time.perf_counter()
    hall_list = _load_hall_list(test_mode=test_mode, test_count=test_count)
    logger.info(
        "timing stage=load_halls hall_count=%d duration_sec=%.2f",
        len(hall_list),
        time.perf_counter() - load_halls_start,
    )

    db_client_start = time.perf_counter()
    supabase = data_to_supabase.get_supabase_client() if upsert_each_date else None
    logger.info(
        "timing stage=db_client enabled=%s duration_sec=%.2f",
        supabase is not None,
        time.perf_counter() - db_client_start,
    )
    target_dates = _load_target_dates_from_env()
    force_rescrape = _parse_bool_env("FORCE_RESCRAPE")
    disable_pre_skip = _parse_bool_env("DISABLE_PRE_SKIP")
    timeout_limit = positive_int_env("CONSECUTIVE_TIMEOUT_LIMIT", 5)
    timeout_breaker = ConsecutiveErrorCircuitBreaker(threshold=timeout_limit)
    if force_rescrape:
        logger.info("force_rescrape=true のため取得済みでも再取得します")
    if disable_pre_skip:
        logger.info("disable_pre_skip=true のため事前スキップを無効化します")

    jst_date = os.getenv("JST_DATE")
    jst_hour = os.getenv("JST_HOUR")
    if jst_date or jst_hour:
        logger.info("実行基準時刻: JST_DATE=%s, JST_HOUR=%s", jst_date, jst_hour)

    frames: list[pd.DataFrame] = []
    target_count = 0
    skipped_count = 0
    scrape_target_count = 0
    scraped_rows = 0
    total_upserted = 0
    hall_error_count = 0
    db_error_count = 0
    warned_prefecture_mismatch_halls: set[str] = set()
    cols = RESULT_COLUMNS

    with sync_playwright() as p:
        browser_start = time.perf_counter()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info(
            "timing stage=browser_startup duration_sec=%.2f",
            time.perf_counter() - browser_start,
        )
        try:
            for i, h in enumerate(hall_list, start=1):
                hall_start = time.perf_counter()
                hall_status = "started"
                encoded_slug = quote(h.slug)
                hall_url = urljoin(config.MAIN_URL, encoded_slug)
                logger.debug("(%d/%d) 処理中: name=%s, prefecture=%s, url=%s", i, len(hall_list), h.name, h.prefecture, hall_url)

                def should_scrape(pref: str, hall: str, date: str) -> bool:
                    nonlocal target_count, skipped_count, scrape_target_count
                    target_count += 1
                    if supabase is None or force_rescrape or disable_pre_skip:
                        scrape_target_count += 1
                        logger.info(
                            "timing stage=db_lookup hall=%s date=%s status=bypassed duration_sec=0.00",
                            hall,
                            date,
                        )
                        logger.info("新規取得対象: hall=%s, date=%s", hall, date)
                        return True
                    lookup_start = time.perf_counter()
                    try:
                        should_skip, existing_count, _ = has_enough_results(
                            supabase,
                            pref,
                            hall,
                            date,
                            min_existing_rows=min_existing_rows,
                        )
                    finally:
                        logger.info(
                            "timing stage=db_lookup hall=%s date=%s duration_sec=%.2f",
                            hall,
                            date,
                            time.perf_counter() - lookup_start,
                        )
                    if should_skip:
                        skipped_count += 1
                        logger.debug(
                            "取得済みのためスキップ: hall=%s, date=%s, existing_count=%d",
                            hall,
                            date,
                            existing_count,
                        )
                        return False
                    scrape_target_count += 1
                    logger.info("新規取得対象: hall=%s, date=%s", hall, date)
                    return True

                try:
                    hall_date_results = extract_result_data_by_dates(
                        page,
                        hall_url,
                        h.period,
                        date_filter=should_scrape,
                        target_dates=target_dates,
                    )
                except Exception as e:
                    hall_error_count += 1
                    hall_status = "error"
                    logger.exception("ホール処理でエラー: %s", e)
                    emit_github_annotation(
                        "error",
                        "ホール収集エラー",
                        f"hall={h.name}, error={type(e).__name__}: {e}",
                    )
                    if isinstance(e, PWTimeout):
                        consecutive_count, is_open, signature = timeout_breaker.record(e)
                        logger.warning(
                            "同種タイムアウト連続数: count=%d limit=%d signature=%s",
                            consecutive_count,
                            timeout_limit,
                            signature,
                        )
                        if is_open:
                            message = (
                                "同種タイムアウトが連続したため収集を打ち切ります: "
                                f"count={consecutive_count}, limit={timeout_limit}, signature={signature}"
                            )
                            logger.error(message)
                            emit_github_annotation("error", "収集サーキットブレーカー作動", message)
                            raise CircuitBreakerOpenError(message) from e
                    else:
                        timeout_breaker.reset()
                    continue
                else:
                    timeout_breaker.reset()
                    hall_status = "completed"
                finally:
                    logger.info(
                        "timing stage=hall hall=%s status=%s duration_sec=%.2f",
                        h.name,
                        hall_status,
                        time.perf_counter() - hall_start,
                    )

                for pref, hall, date, df_hall_date, model_count in hall_date_results:
                    if (
                        h.prefecture
                        and pref
                        and h.prefecture != pref
                        and hall not in warned_prefecture_mismatch_halls
                    ):
                        logger.warning(
                            "config prefecture と site prefecture が違います: config_prefecture=%s, site_prefecture=%s, hall=%s",
                            h.prefecture,
                            pref,
                            hall,
                        )
                        warned_prefecture_mismatch_halls.add(hall)
                    row_count = len(df_hall_date)
                    if row_count == 0:
                        logger.warning("取得対象があるのに rows=0 です: hall=%s, date=%s", hall, date)
                        continue
                    scraped_rows += row_count
                    frames.append(df_hall_date)
                    upserted_rows = 0
                    if upsert_each_date and supabase is not None:
                        db_start = time.perf_counter()
                        db_status = "started"
                        try:
                            upserted_rows = _upsert_hall_date(
                                df_hall_date,
                                supabase,
                                hall=hall,
                                date=date,
                            )
                            total_upserted += upserted_rows
                            db_status = "completed" if upserted_rows else "skipped_empty"
                        except Exception as e:
                            db_error_count += 1
                            db_status = "error"
                            logger.exception("DB登録でエラー: hall=%s, date=%s, error=%s", hall, date, e)
                            emit_github_annotation(
                                "error",
                                "DB登録エラー",
                                f"hall={hall}, date={date}, error={type(e).__name__}: {e}",
                            )
                            continue
                        finally:
                            logger.info(
                                "timing stage=db hall=%s date=%s status=%s duration_sec=%.2f",
                                hall,
                                date,
                                db_status,
                                time.perf_counter() - db_start,
                            )
                    logger.info(
                        "取得・保存完了: hall=%s, date=%s, models=%d, rows=%d, upserted_rows=%d",
                        hall,
                        date,
                        model_count,
                        row_count,
                        upserted_rows,
                    )
        finally:
            browser.close()

    logger.info(
        "取得済み確認完了: target_count=%d, skipped_count=%d, scrape_target_count=%d",
        target_count,
        skipped_count,
        scrape_target_count,
    )

    if scrape_target_count == 0:
        logger.info("全対象が取得済みのため、今回のスクレイピングは実行せず終了します。")

    if frames:
        df_all = pd.concat(frames, ignore_index=True)
    else:
        if scrape_target_count == 0:
            logger.info("取得データが空のため、空DataFrameを出力します。")
        else:
            logger.warning("取得対象があるのに取得データが空のため、空DataFrameを出力します。")
        df_all = pd.DataFrame(columns=cols)

    for c in cols:
        if c not in df_all.columns:
            df_all[c] = pd.NA
    df_all = df_all[cols]
    df_all.to_csv(config.CSV_DIR / "all_result_data.csv", index=False)

    if upsert_each_date and supabase is not None and total_upserted > 0:
        refresh_materialized_views(supabase)
    elif upsert_each_date:
        logger.info("新規登録対象がないためマテビュー更新は呼びません。")

    logger.info(
        "スクレイピング対象確認結果: target_count=%d, skipped_count=%d, "
        "scrape_target_count=%d, scraped_rows=%d, upserted_rows=%d, "
        "hall_error_count=%d, db_error_count=%d",
        target_count,
        skipped_count,
        scrape_target_count,
        scraped_rows,
        total_upserted,
        hall_error_count,
        db_error_count,
    )

    end = time.perf_counter()
    logger.info("全体処理時間: %.2f 秒", end - start)

    quality_issues = build_quality_issues(
        hall_count=len(hall_list),
        target_count=target_count,
        hall_error_count=hall_error_count,
        db_error_count=db_error_count,
    )
    if quality_issues:
        message = "; ".join(quality_issues)
        logger.error("収集品質チェック失敗: %s", message)
        emit_github_annotation("error", "収集品質チェック失敗", message)
        raise RunQualityError(message)

    return df_all


if __name__ == "__main__":
    scraper_all_hall(test_mode=False, test_count=2, min_existing_rows=10)
