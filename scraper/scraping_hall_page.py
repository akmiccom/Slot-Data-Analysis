from playwright.sync_api import sync_playwright
from urllib.parse import quote, urljoin
import pandas as pd
import re
import datetime as dt
import os

import config
from utils import _norm_text
from logger_setup import setup_logger

# =========================
# ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


# =========================
# ページ操作
# =========================
def extract_date_url(hall_url, page, period) -> list[tuple[str, str, str, str]]:
    """
    ホールのメインページから、直近 period 件の日付リンクを取得
    returns: List[(prefecture, hall, date(YYYY-MM-DD), date_url)]
    """

    logger.info(f"ホールのトップページにアクセスします。")
    logger.info(f"url: {hall_url}")
    page.goto(hall_url, timeout=90_000, wait_until="domcontentloaded")

    # ホール名・県名
    hall = _norm_text(page.locator("#content h1").first.text_content())
    pref = _norm_text(page.locator("#content div span.todofuken").first.text_content())
    logger.info("Hall: %s / Pref: %s", hall, pref)

    # スクリーンショット
    page.screenshot(
        path=config.IMG_DIR / f"{hall}_screenshot_hall.jpg", type="jpeg", quality=50
    )

    # 日付リンク
    css = "#content div table tbody tr td a"
    page.wait_for_selector(css, timeout=15_000)
    links = page.locator(css)
    count = links.count()
    logger.debug(f"link取得数: {count}")
    take = min(period, count)
    logger.debug(f"take: {take}")

    date_urls: list[tuple[str, str, str, str]] = []
    for i in range(take):
        href = links.nth(i).get_attribute("href") or ""
        date_text = _norm_text(links.nth(i).inner_text())

        # "YYYY/MM/DD" or "M/D" に対応
        m = re.match(r"(?:(\d{4})/)?(\d{1,2})/(\d{1,2})", date_text)
        if not m:
            logger.warning("日付文字列を解釈できません: %s", date_text)
            continue
        y, mth, d = m.groups()
        if y is None:
            y = str(dt.date.today().year)
        try:
            date_iso = dt.date(int(y), int(mth), int(d)).strftime("%Y-%m-%d")
        except ValueError:
            logger.warning("日付に変換できません: %s", date_text)
            continue

        date_urls.append((pref, hall, date_iso, href))

    logger.info("取得した日付URL: %d 件", len(date_urls))
    if date_urls:
        logger.debug(f"date_urlsの一行目 : {date_urls[0]}")
        for i, date_url in enumerate(date_urls):
            logger.debug(f"{i+1} = {date_url}")

    columns = ["pref", "hall", "date", "date_url"]
    df = pd.DataFrame(date_urls, columns=columns)
    df.to_csv(config.CSV_DIR / f"{hall}_date_urls.csv", index=False)

    return date_urls


if __name__ == "__main__":

    hall = "やすだ東池袋9号店"
    hall = "大山オーシャン"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        hall_url = urljoin(config.MAIN_URL, quote(hall))
        date_urls = extract_date_url(hall_url, page, period=3)
