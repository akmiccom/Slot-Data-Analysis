import os
import pandas as pd

from config import config
from utils.logger_setup import setup_logger


# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)

# =========================
# データベースへの前処理
# =========================
def df_data_clean(df):

    MODELS_ALIAS_MAP = {
        "SミスタージャグラーKK": "ミスタージャグラー",
        "S ミスタージャグラー KK": "ミスタージャグラー",
        "SアイムジャグラーEX": "アイムジャグラーEX-TP",
        "ファンキージャグラー2KT": "ファンキージャグラー2",
        "ジャグラーガールズSS": "ジャグラーガールズ",
        "S ネオアイムジャグラーEX KK": "ネオアイムジャグラーEX",
    }

    COULMNS_RENAME_MAP = {
        "pref": "pref",
        "prefecture": "pref",
        "h_name": "hall",
        "m_name": "model",
        "model_name": "model",
        "date": "date",
        "台番": "unit_no",
        "G数": "game",
        "BB": "bb",
        "RB": "rb",
        "差枚": "medal",
    }

    logger.info("データの前処理を行います。")

    df = df.rename(columns=COULMNS_RENAME_MAP)
    df["model"] = df["model"].replace(MODELS_ALIAS_MAP)
    df["medal"] = df["medal"].str.replace(",", "").astype(int)
    
    # エラー発生行
    # df["game"] = df["game"].str.replace(",", "").astype(int)
    # エラー発生による追加修正
    df["game"] = df["game"].astype(str).str.replace(",", "", regex=False)
    df["game"] = pd.to_numeric(df["game"], errors="coerce")
    df = df.dropna(subset=["game"])
    df["game"] = df["game"].astype(int)

    df.to_csv(config.CSV_DIR / "cleaned_all_result_data.csv", index=False)
    logger.debug(df.info())
    logger.info("データを出力しました。")
    
    return df


if __name__ == "__main__":
    df = pd.read_csv(config.CSV_DIR / "all_result_data.csv")
    df_clean = df_data_clean(df)