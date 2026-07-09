import os
from urllib.parse import urljoin

from playwright.sync_api import Page, TimeoutError as PWTimeout

from config import config
from utils.logger_setup import setup_logger
from utils.utils import _norm_text

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def extract_hall_urls_from_prefecture(page: Page, prefecture_url: str) -> list[tuple[str, str]]:
    """都道府県ページからホール名とホールURL候補を取得する補助関数。

    現行フロー（halls.yaml 起点）は維持し、この関数は段階的移行用として追加する。
    returns: List[(hall_name, hall_url)]
    """
    logger.info("都道府県ページにアクセス: %s", prefecture_url)
    page.goto(prefecture_url, timeout=90_000, wait_until="domcontentloaded")

    css = '#content a[href*="/tag/"]'
    try:
        page.wait_for_selector(css, timeout=15_000)
    except PWTimeout:
        logger.warning("都道府県ページでホールリンクが見つかりません: %s", prefecture_url)
        return []

    links = page.locator(css)
    halls: list[tuple[str, str]] = []
    seen: set[str] = set()
    for i in range(links.count()):
        name = _norm_text(links.nth(i).inner_text())
        href = links.nth(i).get_attribute("href") or ""
        if not name or not href or href in seen:
            continue
        seen.add(href)
        halls.append((name, urljoin(config.MAIN_URL, href)))

    logger.info("都道府県ページからホールリンク抽出: %d 件", len(halls))
    return halls
