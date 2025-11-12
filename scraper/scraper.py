import pandas as pd
from urllib.parse import quote, urljoin
import os
import time
import os
import yaml

import config
from logger_setup import setup_logger
from scraping_result_data import extract_result_data

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


# =========================
# ページ操作
# =========================
def scraper_all_hall(test_mode=False) -> pd.DataFrame:
    start = time.perf_counter()

    # yaml  読み込み
    if not os.path.exists(config.HALLS_YAML):
        raise FileNotFoundError(f"YAMLが見つかりません: {config.HALLS_YAML}")
    with open(config.HALLS_YAML, "r", encoding="utf-8") as f:
        halls_cfg = yaml.safe_load(f).get("halls", [])

    hall_list: list[config.HallInfo] = [
        config.HallInfo(slug=h["slug"], period=int(h["period"])) for h in halls_cfg
    ]

    if test_mode:
        hall_list = hall_list[:2]

    frames: list = []
    for i, h in enumerate(hall_list, start=1):
        try:
            encoded_slug = quote(h.slug)
            hall_url = urljoin(config.MAIN_URL, encoded_slug)
            logger.info("(%d/%d) 処理中: %s", i, len(hall_list), hall_url)
            df_hall = extract_result_data(hall_url, h.period)
            if not df_hall.empty:
                frames.append(df_hall)
        except Exception as e:
            logger.exception("ホール処理でエラー: %s", e)

    df_all = pd.concat(frames, ignore_index=True)

    # 列の順番を固定（下流の処理を安定化）
    cols = ["pref", "hall", "model", "date", "台番", "G数", "BB", "RB", "差枚"]
    for c in cols:
        if c not in df_all.columns:
            df_all[c] = pd.NA
    df_all = df_all[cols]
    df_all.to_csv(config.CSV_DIR / "all_result_data.csv", index=False)

    end = time.perf_counter()
    logger.info("全体処理時間: %.2f 秒", end - start)

    return df_all


if __name__ == "__main__":

    df = scraper_all_hall(test_mode=False)
    # df = df_data_clean(df)

    # conn = sqlite3.connect(config.DB_PATH)
    # # cursor = conn.cursor()

    # # df_to_db.add_model(df, conn, cursor)
    # # df_to_db.add_prefecture_and_hall(df, conn, cursor)
    # # df_to_db.add_data_result(conn, cursor, df)

    # # conn.commit()
    # # conn.close()
