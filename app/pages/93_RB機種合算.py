import pandas as pd
import streamlit as st

from utils import yesterday, n_days_ago
from ui.components import home_link
from ui.filters import filters
from fetch_functions import fetch_results_by_units


column_config = {
    "date": st.column_config.DateColumn(width=80),
    "date_str": st.column_config.Column(width=80),
    "hall": st.column_config.Column(width=140),
    "model": st.column_config.Column(width=70),
    "unit_no": st.column_config.NumberColumn(width=60),
    "rb_rate": st.column_config.NumberColumn(width=50),
    "game": st.column_config.NumberColumn(width=50),
    "medal": st.column_config.NumberColumn(width=50),
}


# --- title ---
page_title = "RB合算確率 機種別検索"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

home_link(position="left")

st.subheader(page_title, divider="rainbow")

st.markdown(
    """
    ページの使い方説明
            """
)

ss = st.session_state
ss.setdefault("start_date", n_days_ago(15))
ss.setdefault("end_date", yesterday)

fi = filters(
    state_prefix="page_a",
    start_date_default = n_days_ago(15),
    visible_fields={
        "pref",
        # "hall",
        "model",
        # "unit_no",
        # "day_last_list",
        # "weekday_int_list",
        "start_date",
        "end_date",
    },
)

# ---- データ読み込み ----
with st.spinner("データ取得中..."):
    df = fetch_results_by_units(
        fi["start_date"],
        fi["end_date"],
        day_last=fi["day_last_list"],
        weekday=fi["weekday_int_list"],
        pref=fi["pref"],
        hall=fi["hall"],
        model=fi["model"],
    )

df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%y-%m-%d %a")

group_index = ["hall", "model", "date_str"]
group_cols = ["game", "medal", "bb", "rb"]
df_sum = df.groupby(group_index).sum(group_cols)
df_mean = df.groupby(group_index).mean(group_cols)

df_sum["game_m"] = df_mean["game"]
df_sum["medal_m"] = df_mean["medal"]
df_sum["rb_rate"] = df_sum.apply(
    lambda r: r["game"] / r["rb"] if r["rb"] != 0 else None, axis=1
)
df_sum["medal_rate"] = (df_sum["game"] * 3 + df_sum["medal"]) / (df_sum["game"] * 3)
df_sum = df_sum[df_sum["medal_rate"] > 1.01]
df_sum = df_sum[df_sum["game"] >= 10000]

with st.expander("RB合算テーブル", expanded=True):
    df_show = df_sum.sort_values(["rb_rate"])[["rb_rate", "game", "medal", "medal_rate"]]
    df_show["rb_rate"] = df_show["rb_rate"].round(1)
    df_show["medal_rate"] = df_show["medal_rate"].round(2)
    show_cols = ["rb_rate", "game", "medal", "medal_rate"]
    # df_show = df_show.reset_index()
    # df_show = df_show.set_index(["hall", "date_str"])
    st.dataframe(df_show[show_cols], column_config=column_config)

home_link(position="right")
