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


def extract_result_data(hall_url: str, period: int = 1):
    """
    ホールurlリストと日付urlリストを受けて、そのホールの対象日・対象機種の全データを返す
    """

    df_frames: list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        date_urls = extract_date_url(hall_url, page, period=period)

        try:
            df_model_urls: list = []
            columns = ["pref", "hall", "date", "date_url", "model_url"]
            for pref, hall, date, date_url in date_urls:
                model_urls = extract_model_url(page, hall, pref, date_url, date)
                if not model_urls:
                    continue
                df_model_url = pd.DataFrame(model_urls, columns=columns)
                df_model_urls.append(df_model_url)

                df_model = extract_model_data(page, model_urls)
                if not df_model.empty:
                    df_frames.append(df_model)

            df_csv = pd.concat(df_model_urls)
            df_csv.to_csv(config.CSV_DIR / f"{pref}_{hall}_model_urls.csv", index=False)

        finally:
            browser.close()
            df_csv = pd.concat(df_frames, ignore_index=True)
            df_csv.to_csv(config.CSV_DIR / f"{pref}_{hall}_result_data.csv", index=False)

        return df_csv


if __name__ == "__main__":

    period = 1
    hall = "グランド-ラ・カータ1111瑞穂店"
    hall = "麗都平塚"
    hall = "エスパス日拓渋谷駅前新館"
    hall = "エスパス日拓渋谷本館"
    hall = "楽園渋谷道玄坂店"
    hall = "楽園渋谷駅前店"
    hall = "p-port-prego-ex池袋南口"
    hall_url = urljoin(config.MAIN_URL, quote(hall))

    extract_result_data(hall_url, period)
