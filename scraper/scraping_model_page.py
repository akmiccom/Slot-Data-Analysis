from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout
import pandas as pd
from urllib.parse import quote, urljoin
import os

from config import config
from utils.logger_setup import setup_logger
from utils.utils import _norm_text, extract_model_name
from scraper.scraping_hall_page import extract_date_url
from scraper.scraping_date_page import extract_model_url

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


# =========================
# ページ操作
# =========================
def goto_with_retry(page: Page, url: str, retries: int = 2) -> None:
    """機種ページへ軽くリトライしながら遷移する。"""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            page.goto(url, timeout=90_000, wait_until="domcontentloaded")
            return
        except Exception as e:
            last_error = e
            logger.warning(
                "機種ページへのアクセスに失敗しました。retry=%d/%d, url=%s, error=%s",
                attempt,
                retries,
                url,
                e,
            )
    if last_error is not None:
        raise last_error


def _log_model_skip(
    hall: str,
    date: str,
    model_url: str,
    url: str,
    error: str | Exception,
) -> None:
    logger.warning(
        "機種データをスキップします: hall=%s, date=%s, model_url=%s, url=%s, error=%s",
        hall,
        date,
        model_url,
        url,
        error,
    )


def extract_model_data(
    page: Page, model_urls: list[tuple[str, str, str, str, str] | tuple[str, str, str, str, str, str]]
) -> pd.DataFrame:
    """
    各機種ページに移動し、台データを DataFrame で返す
    返却列: 台番/G数/差枚/BB/RB + pref/hall/model/date
    """

    frames: list[pd.DataFrame] = []

    for model_url_tuple in model_urls:
        pref, hall, date, date_url, model_url = model_url_tuple[:5]
        canonical_model_name = model_url_tuple[5] if len(model_url_tuple) >= 6 else None
        url = urljoin(date_url, model_url)
        try:
            logger.debug("機種ページにアクセスします。")
            logger.debug("url: %s", url)
            goto_with_retry(page, url, retries=2)

            # スクリーンショット
            # page.screenshot(
            #     path=config.IMG_DIR / f"{hall}_model_page.jpg",
            #     full_page=True,
            #     type="jpeg",
            #     quality=50,
            # )

            # 機種名 (DB保存用は canonical_model_name を優先)
            model = ""
            css = "div.tab_content > h2"
            # css  = "div > h2"
            TARGET_MODEL = "ジャグラー"
            try:
                page.wait_for_selector(css, timeout=10_000)
                h2s = page.locator(css)
                for i in range(h2s.count()):
                    txt = extract_model_name(h2s.nth(i).inner_text())
                    if TARGET_MODEL in txt:
                        model = txt
                        break
                if not model and h2s.count():
                    model = extract_model_name(h2s.nth(i).inner_text())
                logger.debug("機種名(h2): %s", model)
            except PWTimeout:
                logger.warning("機種タイトルが取得できませんでした: %s", url)

            if canonical_model_name:
                if model and canonical_model_name not in model and model not in canonical_model_name:
                    logger.warning(
                        "h2_model と canonical_model_name が想定外に違います: h2_model=%s, canonical_model_name=%s",
                        model,
                        canonical_model_name,
                    )
                else:
                    logger.debug(
                        "DB保存用機種名に canonical_model_name を使用: h2_model=%s, canonical_model_name=%s",
                        model,
                        canonical_model_name,
                    )
                model = canonical_model_name

            # テーブルの取得
            css = "div > div.table_wrap > table > tbody > tr"
            try:
                page.wait_for_selector(css, timeout=15_000)
            except PWTimeout as e:
                _log_model_skip(hall, date, model_url, url, e)
                continue

            rows = page.locator(css)
            if rows.count() == 0:
                _log_model_skip(hall, date, model_url, url, "テーブル行が空")
                continue

            # th行(header)処理
            ths = rows.nth(0).locator("th")
            header = [_norm_text(ths.nth(i).inner_text()) for i in range(ths.count())]
            if not header:
                _log_model_skip(hall, date, model_url, url, "テーブルヘッダーが空")
                continue
            logger.debug(header)
            # td(date)行処理
            table: list[list[str]] = []
            for j in range(rows.count()):
                tds = rows.nth(j).locator("td")
                row = []
                for k in range(tds.count()):
                    row.append(_norm_text(tds.nth(k).inner_text()))
                if row:  # 空行スキップ
                    table.append(row)

            if not table:
                _log_model_skip(hall, date, model_url, url, "テーブルデータが空")
                continue
            for t in table:
                logger.debug(t)

            df = pd.DataFrame(table, columns=header)
            if "台番" not in df.columns:
                _log_model_skip(hall, date, model_url, url, "台番列が見つからない")
                continue
            df = df[~df["台番"].astype(str).str.contains("平均")]
            df["pref"] = pref
            df["hall"] = hall
            df["model"] = model
            df["date"] = date
            logger.debug(
                "機種データ取得成功: hall=%s, date=%s, model=%s, rows=%d",
                hall,
                date,
                model,
                len(df),
            )
            frames.append(df)
        except Exception as e:
            _log_model_skip(hall, date, model_url, url, e)
            continue

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


if __name__ == "__main__":

    period = 1

    hall_name = "グランド-ラ・カータ1111瑞穂店"
    hall_name = "麗都平塚"
    hall_name = "マルハン入間店"
    hall_name = "toho池袋店"
    hall_url = urljoin(config.MAIN_URL, quote(hall_name))

    df_frames: list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        date_urls = extract_date_url(hall_url, page, period=period)

        try:
            df_model_urls: list = []
            columns = ["pref", "hall", "date", "date_url", "model_url", "canonical_model_name"]
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
            df_csv.to_csv(config.CSV_DIR / f"{pref}_{hall}_results.csv", index=False)
