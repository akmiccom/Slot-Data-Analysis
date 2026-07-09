from playwright.sync_api import sync_playwright
from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout
import pandas as pd
from urllib.parse import quote, urljoin
import os

from config import config
from utils.logger_setup import setup_logger
from utils.utils import _norm_text
from utils.target_models import build_alias_to_canonical, match_target_model_detail
from scraper.scraping_hall_page import extract_date_url

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
) -> list[tuple[str, str, str, str, str, str, str, str, str, str]]:
    """
    日付ページから、target_models.yaml に一致する機種リンクを抽出
    returns: List[(pref, hall, date, date_url, model_url, canonical_model_name, raw_model_name, normalized_model_name, match_type, matched_alias)]
    """

    logger.debug("日付ページにアクセス: %s", date_url)
    page.goto(date_url, timeout=90_000, wait_until="domcontentloaded")

    # スクリーンショット
    # page.screenshot(
    #     path=config.IMG_DIR / f"{hall}_date_page.jpg",
    #     full_page=True,
    #     type="jpeg",
    #     quality=50,
    # )

    title = _norm_text(page.locator("h1").first.text_content())
    logger.debug("Page title: %s", title)

    model_urls: list[tuple[str, str, str, str, str, str, str, str, str, str]] = []
    alias_to_canonical = build_alias_to_canonical()
    css_table = "table.kishu"
    first_table = page.locator(css_table).nth(0)

    try:
        page.wait_for_selector(css_table, timeout=10_000)
    except PWTimeout:
        logger.warning("機種リンクが見つかりません: %s", date_url)
        return model_urls

    css_table = "tbody tr td a"
    links = first_table.locator(css_table)
    # links = page.locator(css)
    
    count = links.count()
    for j in range(count):
        model_text = _norm_text(links.nth(j).inner_text())
        href = links.nth(j).get_attribute("href") or ""
        model_match = match_target_model_detail(model_text, alias_to_canonical)
        if model_match:
            logger.debug(
                "対象機種に一致: raw_model_name=%s, normalized_model_name=%s, canonical_model_name=%s, match_type=%s, matched_alias=%s, url=%s",
                model_match.raw_model_name,
                model_match.normalized_model_name,
                model_match.canonical_name,
                model_match.match_type,
                model_match.matched_alias,
                href,
            )
            model_urls.append((
                pref,
                hall,
                date,
                date_url,
                href,
                model_match.canonical_name,
                model_match.raw_model_name,
                model_match.normalized_model_name,
                model_match.match_type,
                model_match.matched_alias,
            ))
        else:
            logger.debug("対象外機種: raw_model_name=%s, url=%s", model_text, href)

    logger.debug("機種リンク抽出: %d 件", len(model_urls))
    if model_urls:
        logger.debug("model_urls[0] = %s", model_urls[0])
        for i, model_url in enumerate(model_urls):
            logger.debug(f"{i+1} = {model_url}")

    return model_urls


if __name__ == "__main__":

    hall = "グランド-ラ・カータ1111瑞穂店"
    hall = "麗都平塚"
    hall = "マルハン入間店"
    hall = "エスパス日拓渋谷本館"
    hall = "エスパス日拓渋谷駅前新館"
    hall_url = urljoin(config.MAIN_URL, quote(hall))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        date_urls = extract_date_url(hall_url, page, period=3)

        df_model_urls: list = []
        columns = ["pref", "hall", "date", "date_url", "model_url", "canonical_model_name", "raw_model_name", "normalized_model_name", "match_type", "matched_alias"]
        for pref, hall, date, date_url in date_urls:
            model_urls = extract_model_url(page, hall, pref, date_url, date)
            df_model_url = pd.DataFrame(model_urls, columns=columns)
            df_model_urls.append(df_model_url)
        df_csv = pd.concat(df_model_urls)
        df_csv.to_csv(config.CSV_DIR / f"{pref}_{hall}_model_urls.csv", index=False)
