from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt

# from fetch_functions import get_supabase_client, _fetch_all_rows

from utils import WEEKDAY_JA, WEEKDAY_JA_TO_INT
from utils import today, yesterday, n_days_ago, prev_month_first

# from utils import calc_grape_rate, predict_setting, continuous_setting
# from utils import auto_height, make_style_val
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units
from utils import validate_dates, rotate_list_by_today


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


def chunk_units_balanced(units, chunk_size=20, min_last=10):
    """
    unitsをchunk_sizeで分割。
    ただし最後のチャンクがmin_last未満なら、直前から移して均す。
    """
    units = list(units)
    chunks = [units[i : i + chunk_size] for i in range(0, len(units), chunk_size)]

    if len(chunks) >= 2 and len(chunks[-1]) < min_last:
        need = min_last - len(chunks[-1])  # 最後に足したい数
        move = min(need, len(chunks[-2]) - 1)  # 直前が空にならないように
        if move > 0:
            chunks[-1] = chunks[-2][-move:] + chunks[-1]
            chunks[-2] = chunks[-2][:-move]

    return chunks


# --- title ---
page_title = "RB合算データ"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader(page_title, divider="rainbow")
st.markdown(
    """
    ページの使い方説明
            """
)

ss = st.session_state
ss.setdefault("start_date", prev_month_first(1))
ss.setdefault("end_date", yesterday)


st.subheader("RB台別合算", divider="rainbow")

ALL = "すべて"
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
    pref = st.selectbox("都道府県", prefectures)
with col2:
    halls = [ALL] + fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
    hall = st.selectbox("halls", halls)
with col3:
    models = [ALL] + fetch_models(pref=pref, hall=None)
    model = st.selectbox("models", models)

col5, col6, col7, col8 = st.columns(4)
with col5:
    start_date = st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col6:
    end_date = st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
with col7:
    day_lasts = [ALL] + rotate_list_by_today([i for i in range(10)])
    day_last = st.selectbox("末尾日", day_lasts)
with col8:
    weekdays = [ALL] + WEEKDAY_JA
    weekday_ja = st.selectbox("曜日", weekdays)
    weekday = WEEKDAY_JA_TO_INT[weekday_ja] if weekday_ja != ALL else ALL


df = fetch_results_by_units(
    start_date, end_date, day_last, weekday, pref=pref, hall=hall, model=model
)
df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%y-%m-%d %a")

group_index = ["hall", "model", "unit_no"]
group_cols = ["game", "medal", "bb", "rb"]
df_sum = df.groupby(group_index).sum(group_cols)
df_mean = df.groupby(group_index).mean(group_cols)

df_sum["game_m"] = df_mean["game"]
df_sum["medal_m"] = df_mean["medal"]
df_sum["rb_rate"] = df_sum.apply(
    lambda r: r["game"] / r["rb"] if r["rb"] != 0 else None, axis=1
)
# df_sum = df_sum[df_sum["game_m"] >= 3000]
# df_sum = df_sum[df_sum["medal_m"] > 0]
df_sum["rb_rate"].round(1)

df_show = df_sum.sort_values(["rb_rate"])[["rb_rate", "game_m", "medal_m"]].round(1)
st.dataframe(df_show, column_config=column_config)


# --- 詳細データ ---
# with st.form("filters", border=True):
#     st.write("詳細表示")
#     col1, col2, col3 = st.columns(3)
#     ALL = "すべて"
#     with col1:
#         halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
#         hall = st.selectbox("halls", halls)
#     with col2:
#         models = fetch_models(pref=pref, hall=None)
#         model = st.selectbox("models", models)
#     with col3:
#         start_date = st.date_input("検索日", value=yesterday)
#         end_date = start_date

#     submitted = st.form_submit_button("表示")

# if not submitted:
#     st.stop()

# df = fetch_results_by_units(start_date, end_date, day_last, weekday, pref=pref, hall=hall, model=model)
# df["total_rate"] = df.apply(lambda r: r["game"] / (r["bb"] + r["rb"]) if (r["bb"] + r["rb"]) != 0 else None, axis=1)
# df["rb_rate"] = df.apply(lambda r: r["game"] / r["rb"] if r["rb"] != 0 else None, axis=1)
# if df.empty:
#     st.text(f"データが存在しません。検索条件の見直しをしてください。")
#     st.stop()

# # df_sum = df.groupby(["date"]).sum()[["game", "medal", "bb", "rb"]]
# df.loc["total"] = df.mean(numeric_only=True)
# df.iloc[-1, 4] = None
# df.iloc[-1, -1] = (df["game"].sum() / df["rb"].sum())
# df = df.round(1)


# df_show = df[["unit_no", "game", "medal", "rb_rate", "total_rate", "bb", "rb"]]
# st.dataframe(df_show, height=auto_height(df_show), hide_index=True)
