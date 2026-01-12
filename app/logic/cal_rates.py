import os
import pandas as pd
import yaml
import json


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

    df["bb_medals"] = df["model"].map(build_mapping("bb", 239))
    df["rb_medals"] = df["model"].map(build_mapping("rb", 95.25))
    df["replay"] = df["model"].map(build_mapping("replay", 0.40475))
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

    return grape_rate


def get_rb_rate(model, setting=5, default=300):
    json_path = r"config/jagglar_rate.json"
    with open(json_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)
    s = model_data.get(model, {}).get(str(setting), {}).get("RB_RATE")
    if isinstance(s, str) and s.startswith("1/"):
        return float(s.split("/")[1])
    return default


def get_total_rate(model, setting=5, default=125):
    json_path = r"config/jagglar_rate.json"
    with open(json_path, "r", encoding="utf-8") as f:
        model_data = json.load(f)
    s = model_data.get(model, {}).get(str(setting), {}).get("TOTAL_RATE")
    if isinstance(s, str) and s.startswith("1/"):
        return float(s.split("/")[1])
    return default