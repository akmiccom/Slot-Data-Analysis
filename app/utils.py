import json
import pandas as pd
import numpy as np
import streamlit as st
from math import log, factorial


# --- 表示 ---
def auto_height(df):
    rows = len(df)
    row_height = 32  # 1行あたりの高さ（目安）
    base_height = 100  # ヘッダ・余白ぶん
    max_height = 1000  # 上限（スクロール防止）
    height = min(base_height + rows * row_height, max_height)
    height = base_height + rows * row_height
    if height < 500:
        height = "auto"
    return height


# --- 条件付き書式設定 ---
def style_val(val):
    if isinstance(val, (int, float)) and val >= 1.02:
        # return "background-color: #ff3366; color: white; font-weight: bold;"   # 赤ピンク系（上位）
        # return "background-color: #ff9933; color: black; font-weight: bold;"   # オレンジ（良い）
        # return "background-color: #ffcc00; color: black; font-weight: bold;"   # 黄色（平均より上）
        # return "background-color: #33cc33; color: black; font-weight: bold;"   # 緑（標準）
        # return "background-color: #66ccff; color: black; font-weight: bold;"  # 水色（やや弱）
        return "background-color: #999999; color: white; font-weight: bold;"  # グレー（低調）
    else:
        return ""


def style_val(val):
    if isinstance(val, (int, float)) and val >= 1.02:
        return "background-color: #66ccff; color: black; font-weight: bold;"  # 水色（やや弱）
    else:
        return ""


def make_style_val(threshold=1.02):
    def style_val(val):
        if isinstance(val, (int, float)) and val >= threshold:
            return "background-color: #999999; color: white; font-weight: bold;"
        return ""

    return style_val


HALLS = [
    "EXA FIRST",
    "コンサートホールエフ成増",
    "楽園大山店",
    "大山オーシャン",
    "楽園池袋店",
    "楽園池袋店グリーンサイド",
    "マルハン大山店",
    "マルハン池袋店",
    "マルハン青梅新町店",
    "スーパースロットサンフラワー⁺",
    "YASUDA9",
]

WEEKDAY_MAP = {
    0: "月",
    1: "火",
    2: "水",
    3: "木",
    4: "金",
    5: "土",
    6: "日",
}


def validate_dates():
    ss = st.session_state
    if ss.end_date < ss.start_date:
        ss.start_date = ss.end_date


def calc_grape_rate(df, cherry=True):
    """
    計算に必要なデータをjsonから取得し
    データにマージしてブドウ確率を計算する
    """
    # json_path = r"config/jagglar_rate.json"
    with open(json_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)
    constants = {k: m.get("grape_constants") for k, m in model_data.items()}
    df_const = pd.DataFrame.from_dict(constants).T
    df_const = df_const.dropna(how="all")
    df_const.index.name = "model"
    df_m = df.merge(df_const, on="model", how="left")
    # st.dataframe(df_m)

    cherry_rate = df_m["cherryOn"] if cherry else df_m["cherryOff"]

    # 分母計算式
    den = (
        -df_m["medal"]
        - (
            df_m["game"] * 3
            - (
                df_m["bb"] * df_m["get_bb"]
                + df_m["rb"] * df_m["get_rb"]
                + df_m["game"] * df_m["replay"]
                + df_m["game"] * cherry_rate
            )
        )
    ) / 8
    # # 行ごとに 0 の場合は NaN に置き換える
    # den = den.replace(0, pd.NA)
    # df_m["grape_rate"] = (df_m["game"] / den) - (
    #     (df_m["game"] / den) * 2
    # )
    df_m["grape_rate"] = -(df_m["game"] / den.replace(0, pd.NA))
    df_m = df_m.drop(df_const.columns, axis=1)
    return df_m


def softmax(logL_dict):
    vals = np.array(list(logL_dict.values()))
    e = np.exp(vals - vals.max())  # 安定化
    return e / e.sum()


# def predict_setting(game, rb, bb, grape_rate, model):
#     """
#     game  : 総ゲーム数
#     rb    : RB回数
#     bb    : BB回数
#     grape : ぶどう回数
#     model : 機種名
#     """

#     # 各機種別 × 設定別の RB確率を float に変換
#     with open(json_path, "r", encoding="utf-8") as f:
#         model_data = json.load(f)
#     # with open("data/json/jagglar_rate.json", encoding="utf-8") as f:
#     #     model_data = json.load(f)

#     rate_table = {}
#     for model, mdata in model_data.items():
#         rate_table[model] = {}
#         for s, vals in mdata.items():
#             if not s.isdigit():
#                 continue

#             d = {}
#             for key in ["RB_RATE", "BB_RATE", "GRAPE_RATE"]:
#                 rate_str = vals.get(key)
#                 if rate_str and rate_str.startswith("1/"):
#                     d[key] = 1.0 / float(rate_str.split("/")[1])
#                 else:
#                     d[key] = None

#             rate_table[model][int(s)] = d

#     if model not in rate_table:
#         return None

#     # ブドウ確率を個数に変換
#     grape_obs = None
#     if grape_rate is None or pd.isna(grape_rate) or grape_rate <= 0:
#         grape_obs = 0
#     else:
#         grape_obs = int(round(game / float(grape_rate)))


#     results = {}
#     for s, rates in rate_table[model].items():
#         p_rb = rates["RB_RATE"]
#         p_bb = rates["BB_RATE"]
#         p_grape = rates["GRAPE_RATE"]

#         # None の設定はスキップ
#         if p_rb is None or p_bb is None or p_grape is None:
#             continue

#         # 期待値
#         lam_rb = game * p_rb
#         lam_bb = game * p_bb
#         lam_grape = game * p_grape

#         # 安全ガード
#         # 極端に小さい対数尤度にして、その設定はほぼ選ばれないようにする
#         if lam_rb <= 0 or lam_bb <= 0:
#             # return None, float("-inf")
#             return None, float("-inf")
#         # bb, rb は 0 以上の整数に揃えておく
#         bb = int(bb)
#         if bb < 0:
#             bb = 0
#         rb = int(rb)
#         if rb < 0:
#             rb = 0

#         # 対数尤度（安定のため log を取る）
#         logL_rb = -lam_rb + rb * log(lam_rb) - log(factorial(rb))
#         logL_bb = -lam_bb + bb * log(lam_bb) - log(factorial(bb))
#         logL_grape = -lam_grape + grape_obs * log(lam_grape) - log(factorial(grape_obs))

#         logL_total = logL_rb + logL_bb + logL_grape
#         results[s] = logL_total

#     best_setting = max(results, key=results.get)
#     return best_setting, results


import json
import math
from math import log, factorial
import pandas as pd
import numpy as np

json_path = r"config/jagglar_rate.json"

def predict_setting(game, rb, bb, grape_rate, model):
    """
    game  : 総ゲーム数
    rb    : RB回数
    bb    : BB回数
    grape_rate : ぶどう確率（1/○ の ○ の側）
    model : 機種名

    戻り値:
        best_setting: 最も尤度が高い設定番号 (int) or None
        results     : {設定番号: 対数尤度} の dict（空の可能性あり）
    """

    # -----------------------------
    # 1) JSON から機種・設定別の確率テーブルを作成
    # -----------------------------
    with open(json_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)

    rate_table: dict[str, dict[int, dict[str, float | None]]] = {}

    for mdl, mdata in model_data.items():
        rate_table[mdl] = {}
        for s, vals in mdata.items():
            if not s.isdigit():
                continue

            d = {}
            for key in ["RB_RATE", "BB_RATE", "GRAPE_RATE"]:
                rate_str = vals.get(key)
                if rate_str and isinstance(rate_str, str) and rate_str.startswith("1/"):
                    try:
                        d[key] = 1.0 / float(rate_str.split("/")[1])
                    except ValueError:
                        d[key] = None
                else:
                    d[key] = None

            rate_table[mdl][int(s)] = d

    # 対象機種がテーブルに無ければ終了
    if model not in rate_table:
        return None, {}

    # -----------------------------
    # 2) 入力値の安全な前処理
    # -----------------------------
    def safe_float(x, default=0.0):
        if x is None or pd.isna(x):
            return default
        try:
            v = float(x)
        except (TypeError, ValueError):
            return default
        return v

    def safe_nonneg_int(x, default=0):
        if x is None or pd.isna(x):
            return default
        try:
            v = int(x)
        except (TypeError, ValueError):
            return default
        return max(v, 0)

    game_f = safe_float(game, default=0.0)
    if game_f < 0:
        game_f = 0.0

    rb_i = safe_nonneg_int(rb, default=0)
    bb_i = safe_nonneg_int(bb, default=0)

    # ぶどう観測回数（grape_obs）の推定
    grape_obs = 0
    gr_f = None
    if grape_rate is not None and not pd.isna(grape_rate):
        try:
            gr_f = float(grape_rate)
        except (TypeError, ValueError):
            gr_f = None

    if gr_f is not None and gr_f > 0 and game_f > 0:
        grape_obs = max(int(round(game_f / gr_f)), 0)
    else:
        grape_obs = 0  # 情報なし扱い

    # -----------------------------
    # 3) 各設定ごとの対数尤度を計算
    # -----------------------------
    results: dict[int, float] = {}

    for s, rates in rate_table[model].items():
        p_rb = rates["RB_RATE"]
        p_bb = rates["BB_RATE"]
        p_grape = rates["GRAPE_RATE"]

        # 確率が欠損している設定はスキップ
        if p_rb is None or p_bb is None or p_grape is None:
            continue

        # 期待値（λ）が 0 以下なら log を取れないのでスキップ
        lam_rb = game_f * p_rb
        lam_bb = game_f * p_bb
        lam_grape = game_f * p_grape

        if lam_rb <= 0 or lam_bb <= 0 or lam_grape <= 0:
            # この設定は尤度を計算できない → 候補から外す
            continue

        # rb, bb, grape_obs は 0 以上の整数
        rb_cnt = max(rb_i, 0)
        bb_cnt = max(bb_i, 0)
        grape_cnt = max(grape_obs, 0)

        # 負の値が入らないよう再チェック
        if rb_cnt < 0 or bb_cnt < 0 or grape_cnt < 0:
            continue

        # 対数尤度（Poisson: -λ + k log λ - log(k!)）
        try:
            logL_rb = -lam_rb + rb_cnt * log(lam_rb) - log(factorial(rb_cnt))
            logL_bb = -lam_bb + bb_cnt * log(lam_bb) - log(factorial(bb_cnt))
            logL_grape = (
                -lam_grape + grape_cnt * log(lam_grape) - log(factorial(grape_cnt))
            )
        except ValueError:
            # 万が一 log の引数が不正になったらこの設定は無視
            continue

        logL_total = logL_rb + logL_bb + logL_grape
        results[s] = logL_total

    # -----------------------------
    # 4) 最尤設定を選んで返す
    # -----------------------------
    if not results:
        # 評価できる設定が一つもなければ「結果なし」
        return None, {}

    best_setting = max(results, key=results.get)
    return best_setting, results


# def continuous_setting(game, rb, bb, grape, model):
#     _, logL = predict_setting(game, rb, bb, grape, model)
#     settings = np.array(list(logL.keys()))
#     weights = softmax(logL)
#     return float((weights * settings).sum())


def continuous_setting(game, rb, bb, grape_rate, model):
    best_setting, logL = predict_setting(game, rb, bb, grape_rate, model)

    # 結果なし → 重み 0 など好きなルールに
    if not logL:
        return 0.0

    settings = np.array(list(logL.keys()), dtype=float)
    logLs = np.array(list(logL.values()), dtype=float)

    # softmax で重み付け
    logLs = logLs - logLs.max()
    w = np.exp(logLs)
    w = w / w.sum()

    weight_setting = float((settings * w).sum())
    return weight_setting



if __name__ == "__main__":
    csv_path = r"data/csv/2025-11-26T23-18_export.csv"
    df_csv = pd.read_csv(csv_path)
    df = calc_grape_rate(df_csv, cherry=True)

    df["pred_setting"] = df.apply(
        lambda r: predict_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        )[0],
        axis=1,
    )

    df["weight_setting"] = df.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    ).round(1)

    # print(df["rb_rate"])
    # print(df["pred_setting"])
    # print(df["weight_setting"])
    print(df)
