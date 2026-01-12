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
    df = df.round(1)

    return df


def preprocess_for_table(df):

    df = preprocess(df)

    df["date"] = df["date"].dt.strftime("%y-%m-%d %a")
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
    df["grape_rate"] = cal_grape_rate(df, cherry=True)
    
    return df