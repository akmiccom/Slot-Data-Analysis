import os
import pandas as pd
import numpy as np
import yaml

from config import config
from utils.logger_setup import setup_logger


# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def build_mapping(key, default):
    # yaml  読み込み
    yaml_path = "app/grape_constants.yml"
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAMLが見つかりません: {yaml_path}")
    with open(yaml_path, "r", encoding="utf-8") as f:
        GRAPE_CONSTANTS = yaml.safe_load(f)
    "ブドウ計算用の機種別確率、獲得枚数、小役確率のマッピングを作成"
    return {
        k: v.get("grape_contents", {}).get(key, default)
        for k, v in GRAPE_CONSTANTS.items()
    }


# =========================
# データベースへの前処理
# =========================
def df_data_clean(df):

    # TODO: スクレイピング時の指定機種方式と二重管理にならないよう、
    # 将来的には config/target_models.yaml に寄せる。
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

    required_cols = ["pref", "hall", "model", "date", "unit_no", "game", "bb", "rb", "medal"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning("前処理に必要な列が不足しています: %s", missing_cols)
        return pd.DataFrame(columns=required_cols)
    if df.empty:
        logger.warning("前処理対象データが空です。")
        return df[required_cols].copy()

    df["model"] = df["model"].replace(MODELS_ALIAS_MAP)

    # エラー発生行
    # df["game"] = df["game"].str.replace(",", "").astype(int)
    # df["medal"] = df["medal"].str.replace(",", "").astype(int)
    # エラー発生による追加修正
    # df["game"] = df["game"].astype(str).str.replace(",", "", regex=False)
    # df["game"] = pd.to_numeric(df["game"], errors="coerce")
    # df = df.dropna(subset=["game"])
    # df["game"] = df["game"].astype(int)
    # エラー発生による追加修正 その2
    num_cols = [
        "game",
        "medal",
        "bb",
        "rb",
    ]
    for col in num_cols:
        df[col] = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=[col])
        df[col] = df[col].astype(int)

    # 予測RB回数を計算して列修正
    calc_rb_count(df)

    # 予測メダル数を計算して列修正
    calc_medal(df)

    duplicate_keys = ["pref", "hall", "model", "date", "unit_no"]
    duplicate_count = df.duplicated(subset=duplicate_keys, keep=False).sum()
    logger.info("clean後の重複件数(%s): %d 件", duplicate_keys, duplicate_count)
    if duplicate_count:
        df = df.drop_duplicates(subset=duplicate_keys, keep="last")
        logger.info("重複除去後の件数: %d 件", len(df))

    df.to_csv(config.CSV_DIR / "cleaned_all_result_data.csv", index=False)
    logger.debug(df.info())
    logger.info("データを出力しました。")

    return df


def calc_rb_count(df):
    """
    予測メダル枚数を計算して列修正する関数。特定のホールに対してのみ適用される。
    エラー発生時は、greape_contents.yamlの対象機種を確認する
    """

    specific_halls = ["パーラーディオス下赤塚本店"]
    df_specific_halls = df[(df["hall"].isin(specific_halls))].copy()

    df_specific_halls["bb_medals"] = df_specific_halls["model"].map(
        build_mapping("bb", 239)
    )
    df_specific_halls["rb_medals"] = df_specific_halls["model"].map(
        build_mapping("rb", 95.25)
    )
    df_specific_halls["replay"] = df_specific_halls["model"].map(
        build_mapping("replay", 0.40475)
    )
    df_specific_halls["cherry"] = df_specific_halls["model"].map(
        build_mapping("cherryOff", 0.06)
    )
    df_specific_halls["grape"] = 1 / 6 * 8

    out_bb = df_specific_halls["bb_medals"] * df_specific_halls["bb"]
    out_replay = df_specific_halls["replay"] * df_specific_halls["game"]
    out_cherry = df_specific_halls["cherry"] * df_specific_halls["game"]
    out_grape = df_specific_halls["grape"] * df_specific_halls["game"]
    diff_medal = df_specific_halls["medal"]

    in_medal = df_specific_halls["game"] * 3

    df_specific_halls["rb_out"] = (
        in_medal + diff_medal - (out_bb + out_replay + out_cherry + out_grape)
    )

    df_specific_halls["rb_calc"] = (
        (df_specific_halls["rb_out"] / df_specific_halls["rb_medals"])
        .round()
        .astype(int)
    )

    df.loc[df_specific_halls.index, "rb"] = df_specific_halls["rb_calc"]
    
    
def calc_medal(df):
    """
    予測RB回数を計算して列修正する関数。特定のホールに対してのみ適用される。
    エラー発生時は、greape_contents.yamlの対象機種を確認する
    """

    specific_halls = ["ウイングあすと長町店"]
    df_specific_halls = df[(df["hall"].isin(specific_halls))].copy()

    df_specific_halls["bb_medals"] = df_specific_halls["model"].map(
        build_mapping("bb", 239)
    )
    df_specific_halls["rb_medals"] = df_specific_halls["model"].map(
        build_mapping("rb", 95.25)
    )
    df_specific_halls["replay"] = df_specific_halls["model"].map(
        build_mapping("replay", 0.40475)
    )
    df_specific_halls["cherry"] = df_specific_halls["model"].map(
        build_mapping("cherryOff", 0.06)
    )
    df_specific_halls["grape"] = 1 / 6 * 8

    out_bb = df_specific_halls["bb_medals"] * df_specific_halls["bb"]
    out_rb = df_specific_halls["rb_medals"] * df_specific_halls["rb"]
    out_replay = df_specific_halls["replay"] * df_specific_halls["game"]
    out_cherry = df_specific_halls["cherry"] * df_specific_halls["game"]
    out_grape = df_specific_halls["grape"] * df_specific_halls["game"]

    in_medal = df_specific_halls["game"] * 3

    df_specific_halls["medal_calc"] = (
        (out_bb + out_rb + out_replay + out_cherry + out_grape) - in_medal
    ).round().astype(int)
    
    logger.debug("補正対象ホールのmedal計算結果:\n%s", df_specific_halls)

    df.loc[df_specific_halls.index, "medal"] = df_specific_halls["medal_calc"]


if __name__ == "__main__":

    df = pd.read_csv(config.CSV_DIR / "all_result_data.csv")
    df_clean = df_data_clean(df)
