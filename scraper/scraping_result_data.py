from playwright.sync_api import sync_playwright
# from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout
import pandas as pd
from urllib.parse import quote, urljoin
import os

from config import config
from utils.logger_setup import setup_logger
from utils.utils import _norm_text, extract_model_name
from scraper.scraping_hall_page import extract_date_url
from scraper.scraping_date_page import extract_model_url
from scraper.scraping_model_page import extract_model_data

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)

RESULT_COLUMNS = ["pref", "hall", "model", "date", "台番", "G数", "BB", "RB", "差枚"]
MODEL_URL_COLUMNS = ["pref", "hall", "date", "date_url", "model_url", "canonical_model_name", "raw_model_name", "normalized_model_name", "match_type", "matched_alias"]

def extract_result_data_by_dates(
    page,
    hall_url: str,
    period: int = 1,
    date_filter=None,
) -> list[tuple[str, str, str, pd.DataFrame, int]]:
    """ホール×日付単位で結果データを取得する。

    returns: List[(pref, hall, date, df_result, model_count)]
    """
    date_urls = extract_date_url(hall_url, page, period=period)
    results: list[tuple[str, str, str, pd.DataFrame, int]] = []

    for pref, hall, date, date_url in date_urls:
        if date_filter is not None and not date_filter(pref, hall, date):
            continue

        model_urls = extract_model_url(page, hall, pref, date_url, date)
        model_count = len(model_urls)
        if not model_urls:
            logger.warning("機種URLが取得できませんでした: %s / %s / %s", pref, hall, date)
            results.append((pref, hall, date, pd.DataFrame(columns=RESULT_COLUMNS), model_count))
            continue

        df_model_urls = pd.DataFrame(model_urls, columns=MODEL_URL_COLUMNS)
        df_model_urls.to_csv(
            config.CSV_DIR / f"{pref}_{hall}_{date}_model_urls.csv",
            index=False,
        )

        df_result = extract_model_data(page, model_urls)
        if df_result.empty:
            logger.warning("結果データが空です: %s / %s / %s", pref, hall, date)
            df_result = pd.DataFrame(columns=RESULT_COLUMNS)
        df_result.to_csv(
            config.CSV_DIR / f"{pref}_{hall}_{date}_result_data.csv",
            index=False,
        )
        results.append((pref, hall, date, df_result, model_count))

    return results


def extract_result_data(hall_url: str, period: int = 1):
    """
    ホールurlリストと日付urlリストを受けて、そのホールの対象日・対象機種の全データを返す
    """

    df_frames: list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        date_urls = extract_date_url(hall_url, page, period=period)

        pref = hall = "unknown"
        try:
            df_model_urls: list = []
            for pref, hall, date, date_url in date_urls:
                model_urls = extract_model_url(page, hall, pref, date_url, date)
                if not model_urls:
                    continue
                df_model_url = pd.DataFrame(model_urls, columns=MODEL_URL_COLUMNS)
                df_model_urls.append(df_model_url)

                df_model = extract_model_data(page, model_urls)
                if not df_model.empty:
                    df_frames.append(df_model)

            if df_model_urls:
                df_model_urls_result = pd.concat(df_model_urls, ignore_index=True)
            else:
                logger.warning("機種URLが取得できませんでした: %s", hall_url)
                df_model_urls_result = pd.DataFrame(columns=MODEL_URL_COLUMNS)
            df_model_urls_result.to_csv(config.CSV_DIR / f"{pref}_{hall}_model_urls.csv", index=False)

        finally:
            browser.close()
            if df_frames:
                df_result = pd.concat(df_frames, ignore_index=True)
            else:
                logger.warning("結果データが取得できませんでした: %s", hall_url)
                df_result = pd.DataFrame(columns=RESULT_COLUMNS)
            df_result.to_csv(config.CSV_DIR / f"{pref}_{hall}_result_data.csv", index=False)

        return df_result


if __name__ == "__main__":

    period = 2
    hall = "パーラーディオス下赤塚本店"
    hall_url = urljoin(config.MAIN_URL, quote(hall))

    extract_result_data(hall_url, period)
