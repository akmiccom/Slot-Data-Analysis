from playwright.sync_api import sync_playwright
from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout
import pandas as pd
from urllib.parse import quote, urljoin
import os

import config
from logger_setup import setup_logger
from utils import _norm_text
from scraping_hall_page import extract_date_url

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


# =========================
# ページ操作
# =========================
def extract_model_url(
    page: Page, hall: str, pref: str, date_url: str, date: str
) -> list[tuple[str, str, str, str, str]]:
    """
    日付ページから、"ジャグラー" を含む機種リンクを抽出
    returns: List[(pref, hall, date, date_url, model_url)]
    """

    logger.info("日付ページにアクセス: %s", date_url)
    page.goto(date_url, timeout=90_000, wait_until="domcontentloaded")

    # スクリーンショット
    page.screenshot(
        path=config.IMG_DIR / f"{hall}_screenshot_date.jpg", type="jpeg", quality=50
    )

    title = _norm_text(page.locator("h1").first.text_content())
    logger.info("Page title: %s", title)

    model_urls: list[tuple[str, str, str, str, str]] = []
    css = "table.kishu tbody tr td a"
    try:
        page.wait_for_selector(css, timeout=10_000)
    except PWTimeout:
        logger.warning("機種リンクが見つかりません: %s", date_url)
        return model_urls

    links = page.locator(css)
    count = links.count()
    for j in range(count):
        model_text = _norm_text(links.nth(j).inner_text())
        if "ジャグラー" in model_text:
            href = links.nth(j).get_attribute("href") or ""
            model_urls.append((pref, hall, date, date_url, href))

    logger.info("機種リンク抽出: %d 件", len(model_urls))
    if model_urls:
        logger.debug("model_urls[0] = %s", model_urls[0])
        for i, model_url in enumerate(model_urls):
            logger.debug(f"{i+1} = {model_url}")

    return model_urls


if __name__ == "__main__":

    hall = "やすだ東池袋9号店"
    hall = "大山オーシャン"
    hall_url = urljoin(config.MAIN_URL, quote(hall))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        date_urls = extract_date_url(hall_url, page, period=3)

        df_concat: list = []
        columns = ["pref", "hall", "date", "date_url", "model_url"]
        for pref, hall, date, date_url in date_urls:
            model_urls = extract_model_url(page, hall, pref, date_url, date)
            df_tmp = pd.DataFrame(model_urls, columns=columns)
            df_concat.append(df_tmp)
        df = pd.concat(df_concat)
        df.to_csv(config.CSV_DIR / f"{hall}_model_urls.csv", index=False)
