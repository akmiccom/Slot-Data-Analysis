import os
import pandas as pd
import yaml
from utils import WEEKDAY_MAP
from data_from_supabase import fetch

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


def cal_grape_rate(df, cherry=True):
    "ブドウ確率の計算"
    if cherry:
        cherry = df["model"].map(build_mapping("cherryOn", 0.06))
    else:
        cherry = df["model"].map(build_mapping("cherryOff", 0.06))
    payout = (
        df["bb"] * df["bb_medals"]
        + df["rb"] * df["rb_medals"]
        + df["game"] * df["replay"]
        + df["game"] * cherry
    )
    coin_in = df["game"] * 3
    denominator = (-(df["medal"] + (coin_in - payout))) / 8
    grape_rate = (df["game"] / denominator) - ((df["game"] / denominator) * 2)

    return grape_rate.round(3)


# groupby 用のカラムを追加
def df_preprocess(df):
    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.day
    df["weekday_num"] = df["date"].dt.weekday
    df["weekday"] = df["weekday_num"].map(WEEKDAY_MAP)
    df["day_last"] = df["day"].astype(str).str[-1]
    df["date"] = df["date"].dt.strftime("%m-%d %a")
    
    df["bb_medals"] = df["model"].map(build_mapping("bb", 239))
    df["rb_medals"] = df["model"].map(build_mapping("rb", 95.25))
    df["replay"] = df["model"].map(build_mapping("replay", 0.40475))
    df["grape_r"] = cal_grape_rate(df, cherry=True).round(2)
    df["cherry_on_grape"] = cal_grape_rate(df, cherry=False).round(2)

    
    return df
    
    
if __name__ == "__main__":
    
    start = "2025-11-15"
    end = "2025-11-15"
    hall = "楽園ハッピーロード大山"
    model = "マイジャグラーV"
    df = fetch("result_joined", start, end, hall, model)
    df = df_preprocess(df)

    print(df.hall.unique())
    print(df.model.unique())
    print(df.date.unique())
    print(df.head())
    # print(df.tail())