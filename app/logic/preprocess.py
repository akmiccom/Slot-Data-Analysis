import os
import pandas as pd
import numpy as np

from logic.cal_rates import cal_grape_rate
from logic.cal_rates import get_rb_rate, get_total_rate

from config.constants import RB_MIN, TOTAL_MIN


def reorder_columns(df, first_cols):
    first = [c for c in first_cols if c in df.columns]
    rest = [c for c in df.columns if c not in first]
    return df[first + rest]


# Perprocess df
def preprocess(df):

    df["date"] = pd.to_datetime(df["date"])
    # df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d %a')
    df = df.sort_values(["unit_no", "date"], ascending=[True, False])

    df["bb_rate"] = df["game"] / df["bb"].replace(0, np.nan)
    df["rb_rate"] = df["game"] / df["rb"].replace(0, np.nan)
    bb_rb = df["bb"] + df["rb"]
    df["total_rate"] = df["game"] / bb_rb.replace(0, np.nan)
    df["grape_rate"] = cal_grape_rate(df, cherry=True)
    df = df.round(1)

    return df


def preprocess_for_table(df):

    df = preprocess(df)

    df["date_str"] = df["date"].dt.strftime("%y-%m-%d %a")
    # df["weekday"] = pd.to_datetime(df["date"]).dt.strftime("%a")

    df["grape_rate"] = cal_grape_rate(df, cherry=True)
    df = df.round(3)

    drop_list = ["day_last", "weekday", "bb_medals", "rb_medals", "replay"]
    df = df.drop(drop_list, axis=1)
    # df = reorder_columns(df, ["date"])
    df = df.set_index(["prefecture", "hall", "model"])

    return df


def preprocess_for_chart(df, model):

    df = preprocess(df)

    df = df.copy()
    df["date_str"] = df["date"].dt.strftime("%y-%m-%d %a")

    RB_MAX = get_rb_rate(model, setting=1)
    df["rb_rate_plot"] = np.where(
        df["rb_rate"].between(RB_MIN, RB_MAX), df["rb_rate"], np.nan
    )
    df["total_rate_plot"] = np.where(
        df["total_rate"].between(TOTAL_MIN, RB_MAX), df["total_rate"], np.nan
    )

    return df


def preprocess_for_rb_rate(df):

    df = preprocess(df)
    # df["date"] = df["date"].dt.strftime("%y-%m-%d %a")

    group_index = ["hall", "model", "unit_no"]
    group_cols = ["game", "medal", "bb", "rb"]
    df_sum = df.groupby(group_index).sum(group_cols)
    df_sum["count"] = df.groupby(["hall", "model", "unit_no"]).size()
    # df_sum = df.groupby(group_index).size().reset_index(name="n_records")

    df_sum["rb_rate"] = df_sum.apply(
        lambda r: r["game"] / r["rb"] if r["rb"] != 0 else None, axis=1
    )
    df_sum["medal_rate"] = (df_sum["game"] * 3 + df_sum["medal"]) / (df_sum["game"] * 3)
    df_sum = df_sum[df_sum["medal_rate"] > 1.0]
    df_sum = df_sum[df_sum["count"] > df_sum["count"].quantile(0.05)]
    df_sum = df_sum[df_sum["game"] >= 15000]

    df_sum = df_sum.sort_values(["rb_rate"])
    df_sum["rb_rate"] = df_sum["rb_rate"].round(1)
    df_sum["medal_rate"] = df_sum["medal_rate"].round(2)
    df_sum = df_sum.reset_index()
    cols = ["count", "rb_rate", "game", "medal", "medal_rate"]
    df_sum = df_sum[["hall", "unit_no"] + cols]

    return df_sum
