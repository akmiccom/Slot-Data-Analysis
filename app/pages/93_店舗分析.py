import os
import streamlit as st
import pandas as pd
import numpy as np

from config.dates import yesterday, prev_month_first
from ui.filters import filters_for_history
from ui.filters import filters
from ui.components import home_link
from ui.charts import charts_on_unit_no

from fetch_functions import fetch_results_by_units
from ui.helpers import order_by_priority
from config.constants import PRIORITY_MODELS


# page_config
page_title = os.path.splitext(os.path.basename(__file__))[0]
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

home_link(position="left")

st.header(page_title)

ss = st.session_state
ss.setdefault("start_date", prev_month_first(3))
ss.setdefault("end_date", yesterday)

# filters
fi = filters(
    state_prefix="page_a",
    start_date_default=prev_month_first(3),
    visible_fields={
        "pref",
        "hall",
        # "model",
        # "unit_no",
        # "day_last_list",
        # "weekday_int_list",
        "start_date",
        # "end_date",
    },
)

df = fetch_results_by_units(
    fi["start_date"],
    # fi["end_date"],
    yesterday,
    pref=fi["pref"],
    hall=fi["hall"],
)

if df is None or df.empty:
    st.info("選択した条件のデータがありません。")
    home_link(position="left")
    st.stop()

c1, c2 = st.columns(2, gap="small")
box_height_1 = 320
box_height_2 = 500
with c1:
    expander_title = "機種別集計"
    df_tmp = df.copy()
    df_model = df_tmp.groupby(["model"], as_index=True).agg(
        n_units=("unit_no", "nunique"),
        game=("game", "sum"),
        medal=("medal", "sum"),
    )

    base = df_model["game"] * 3
    df_model["payout"] = np.where(base != 0, 1 + df_model["medal"] / base, np.nan)
    df_model = df_model.sort_values("medal", ascending=False)

    with st.expander(expander_title, expanded=True):
        st.dataframe(df_model, width="stretch", height=box_height_1, hide_index=False)

    expander_title = "末尾日別集計"
    df_tmp = df.copy()
    df_day_last = df_tmp.groupby(["day_last"], as_index=True).agg(
        n_units=("unit_no", "nunique"),
        game=("game", "sum"),
        medal=("medal", "sum"),
        n_days=("date", "nunique"),
    )

    base = df_day_last["game"] * 3
    df_day_last["payout"] = np.where(base != 0, 1 + df_day_last["medal"] / base, np.nan)
    df_day_last = df_day_last.sort_values("payout", ascending=False)
    with st.expander(expander_title, expanded=True):
        st.dataframe(df_day_last, width="stretch", height="auto", hide_index=False)


with c2:
    expander_title = "曜日別集計"
    df_tmp = df.copy()
    df_tmp["weekday"] = pd.to_datetime(df_tmp["date"]).dt.day_name()

    df_weekday = df_tmp.groupby(["weekday"], as_index=True).agg(
        n_units=("unit_no", "nunique"),
        # days=("date", "nunique"),
        game=("game", "sum"),
        medal=("medal", "sum"),
    )

    base = df_weekday["game"] * 3
    df_weekday["payout"] = np.where(base != 0, 1 + df_weekday["medal"] / base, np.nan)
    df_weekday = df_weekday.sort_values("payout", ascending=False)
    with st.expander(expander_title, expanded=True):
        st.dataframe(df_weekday, width="stretch", height=box_height_1, hide_index=False)

    expander_title = "台別集計"
    df_unit = df.groupby(["model", "unit_no"], as_index=True).agg(
        game=("game", "sum"),
        medal=("medal", "sum"),
        # bb=("bb", "sum"),
        rb=("rb", "sum"),
        days=("date", "nunique"),
    )

    base = df_unit["game"] * 3
    df_unit["payout"] = np.where(base != 0, 1 + df_unit["medal"] / base, np.nan)
    df_unit["rb_prob"] = np.where(
        df_unit["rb"] != 0, df_unit["game"] / df_unit["rb"], np.nan
    )

    df_unit = df_unit.sort_values("payout", ascending=False)
    df_unit = df_unit[["game", "medal", "payout", "rb_prob"]].head(50)
    with st.expander(expander_title, expanded=True):
        st.dataframe(df_unit, width="stretch", height="auto", hide_index=False)


expander_title = "曜日別集計"
df_tmp = df.copy()

# 台ごとのRB確率
df_unit = df_tmp.groupby(["hall", "day", "unit_no"], as_index=False).agg(
    game=("game", "sum"),
    rb=("rb", "sum"),
)

df_unit["rb_prob_unit"] = np.where(
    df_unit["rb"] != 0, df_unit["game"] / df_unit["rb"], np.nan
)

# 台ごとのRBProb標準偏差を hall × day に追加
rb_std = df_unit.groupby(["hall", "day"])["rb_prob_unit"].std().rename("rb_prob_std")


df_day = df_tmp.groupby(["hall", "day"], as_index=True).agg(
    game=("game", "sum"),
    medal=("medal", "sum"),
    #   bb=("bb", "sum"),
    rb=("rb", "sum"),
    n_days=("date", "nunique"),
    n_units=("unit_no", "nunique"),
)

base = df_day["game"] * 3
df_day["payout"] = np.where(base != 0, 1 + df_day["medal"] / base, np.nan)
df_day["rb_prob"] = np.where(df_day["rb"] != 0, df_day["game"] / df_day["rb"], np.nan)
# df_day["bb_prob"] = np.where(df_day["bb"] != 0, df_day["game"] / df_day["bb"], np.nan)
df_day = df_day.join(rb_std)
df_day["avg_game"] = np.where(
    df_day["n_days"] != 0, df_day["game"] / df_day["n_days"], np.nan
)
df_day["avg_medal"] = np.where(
    df_day["n_days"] != 0, df_day["medal"] / df_day["n_days"], np.nan
)

df_day = df_day.sort_values("payout", ascending=False)

show_cols = [
    "n_days",
    "n_units",
    "game",
    "medal",
    "payout",
    "rb_prob",
    "rb_prob_std",
    "avg_game",
    "avg_medal",
]

with st.expander(expander_title, expanded=True):
        st.dataframe(df_day[show_cols], width="stretch", height="auto", hide_index=False)