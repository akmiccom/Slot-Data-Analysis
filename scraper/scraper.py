import pandas as pd
from urllib.parse import quote, urljoin
import os
import time
import yaml
from playwright.sync_api import sync_playwright

from config import config
from utils.logger_setup import setup_logger
from scraper.scraping_result_data import RESULT_COLUMNS, extract_result_data_by_dates
from scraper.preprocess_for_db import df_data_clean
from scraper import data_to_supabase
from scraper.materialized_views import refresh_materialized_views
from scraper.supabase_lookup import has_enough_results

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


# =========================
# ページ操作
# =========================
def _load_hall_list(test_mode: bool = False, test_count: int = 2) -> list[config.HallInfo]:
    if not os.path.exists(config.HALLS_YAML):
        raise FileNotFoundError(f"YAMLが見つかりません: {config.HALLS_YAML}")
    with open(config.HALLS_YAML, "r", encoding="utf-8") as f:
        halls_cfg = yaml.safe_load(f).get("halls", [])

    hall_list: list[config.HallInfo] = [
        config.HallInfo(slug=h["slug"], period=int(h["period"])) for h in halls_cfg
    ]

    if test_mode:
        hall_list = hall_list[:test_count]
        logger.info("*********** テストモードで実行しています。 **********")
    return hall_list


def _upsert_hall_date(df_hall_date: pd.DataFrame, supabase) -> int:
    if df_hall_date.empty:
        logger.warning("空データのためDB登録をスキップします。")
        return 0

    df_clean = df_data_clean(df_hall_date)
    if df_clean.empty:
        logger.warning("前処理後のデータが空のためDB登録をスキップします。")
        return 0

    data_to_supabase.add_model(df_clean, supabase)
    data_to_supabase.add_prefecture_and_hall(df_clean, supabase)
    return data_to_supabase.add_data_result(df_clean, supabase)


def scraper_all_hall(
    test_mode: bool = False,
    test_count: int = 2,
    min_existing_rows: int = 10,
    upsert_each_date: bool = True,
) -> pd.DataFrame:
    start = time.perf_counter()
    hall_list = _load_hall_list(test_mode=test_mode, test_count=test_count)
    supabase = data_to_supabase.get_supabase_client() if upsert_each_date else None

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
    cols = RESULT_COLUMNS

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            for i, h in enumerate(hall_list, start=1):
                encoded_slug = quote(h.slug)
                hall_url = urljoin(config.MAIN_URL, encoded_slug)
                logger.info("(%d/%d) 処理中: %s", i, len(hall_list), hall_url)

                def should_scrape(pref: str, hall: str, date: str) -> bool:
                    nonlocal target_count, skipped_count, scrape_target_count
                    target_count += 1
                    if supabase is None:
                        scrape_target_count += 1
                        return True
                    should_skip, existing_count, _ = has_enough_results(
                        supabase,
                        pref,
                        hall,
                        date,
                        min_existing_rows=min_existing_rows,
                    )
                    if should_skip:
                        skipped_count += 1
                        logger.info(
                            "取得済みのためスキップ: hall=%s, date=%s, existing_count=%d",
                            hall,
                            date,
                            existing_count,
                        )
                        return False
                    scrape_target_count += 1
                    return True

                try:
                    hall_date_results = extract_result_data_by_dates(
                        page,
                        hall_url,
                        h.period,
                        date_filter=should_scrape,
                    )
                except Exception as e:
                    logger.exception("ホール処理でエラー: %s", e)
                    continue

                for pref, hall, date, df_hall_date, model_count in hall_date_results:
                    row_count = len(df_hall_date)
                    logger.info(
                        "取得結果: hall=%s, date=%s, models=%d, rows=%d",
                        hall,
                        date,
                        model_count,
                        row_count,
                    )
                    if df_hall_date.empty:
                        logger.warning("空データです: hall=%s, date=%s", hall, date)
                        continue
                    scraped_rows += row_count
                    frames.append(df_hall_date)
                    if upsert_each_date and supabase is not None:
                        try:
                            total_upserted += _upsert_hall_date(df_hall_date, supabase)
                        except Exception as e:
                            logger.exception("DB登録でエラー: hall=%s, date=%s, error=%s", hall, date, e)
        finally:
            browser.close()

    if scrape_target_count == 0:
        logger.info("全対象が取得済みのため、今回のスクレイピングは実行せず終了します。")

    if frames:
        df_all = pd.concat(frames, ignore_index=True)
    else:
        logger.warning("取得データが空のため、空DataFrameを出力します。")
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
        "scrape_target_count=%d, scraped_rows=%d, upserted_rows=%d",
        target_count,
        skipped_count,
        scrape_target_count,
        scraped_rows,
        total_upserted,
    )

    end = time.perf_counter()
    logger.info("全体処理時間: %.2f 秒", end - start)
    return df_all


if __name__ == "__main__":
    scraper_all_hall(test_mode=False, test_count=2, min_existing_rows=10)
