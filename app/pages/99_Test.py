import streamlit as st
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import time

from data_from_supabase import get_supabase_client
from data_from_supabase import _fetch_all_rows
from data_from_supabase import fetch, fetch_latest, fetch_halls, fetch_models


def begin_of_month_to_end_of_month(months=3, past_n_days=5):
    """期間を開始日を指定月数の1日から、n月前の月末からm日まで"""
    today = datetime.date.today()
    year, month = today.year, today.month
    yesterday = today - datetime.timedelta(days=1)
    n_d_ago = today - datetime.timedelta(days=past_n_days)
    this_month_first = datetime.date(year, month, 1)
    n_m_ago_first = this_month_first - relativedelta(months=months)

    return n_m_ago_first, n_d_ago, yesterday, today


def pre_process_first(df, is_win=1.03):
    """データに必要な列を追加する"""
    # df["date"] = pd.to_datetime(df["date"])
    # df["weekday"] = df["date"].dt.day_name()
    df["bb_rate"] = (df["game"] / df["bb"]).round(1)
    df["rb_rate"] = (df["game"] / df["rb"]).round(1)
    df["total_rate"] = (df["game"] / (df["bb"] + df["rb"])).round(1)
    df["medal_rate"] = ((df["game"] * 3 + df["medal"]) / (df["game"] * 3)).round(3)
    df["is_win"] = df["medal_rate"] > is_win
    # df["day"] = df["date"].dt.day
    # df["day_last"] = df["day"].astype(str).str[-1].astype(int)
    # df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d-%a")
    return df


def pre_process_groupe(df, group_targets):
    grouped = df.groupby(group_targets)

    unit_count = grouped["game"].count()
    unit_count.name = "count"

    is_win = grouped["is_win"].sum()
    win_rate = (is_win / unit_count).round(2)
    win_rate.name = "win_rate"

    game_sum = grouped["game"].sum()
    game_mean = grouped["game"].mean().round(1)
    game_mean.name = "game_m"

    medals = grouped["medal"].sum()
    medal_mean = grouped["medal"].mean().round(1)
    medal_mean.name = "medal_m"

    rb = grouped["rb"].sum()
    rb_rate = (game_sum / rb).round(1)
    rb_rate.name = "rb_rate"

    cv = (grouped["rb"].std() / grouped["rb"].mean()).round(3)
    cv.name = "cv"

    bb = grouped["bb"].sum()
    total_rate = (game_sum / (bb + rb)).round(1)
    total_rate.name = "total_rate"

    medal_rate = ((game_sum * 3 + medals) / (game_sum * 3)).round(3)
    medal_rate.name = "medal_rate"

    for_concat_list = [
        game_sum,
        game_mean,
        unit_count,
        bb,
        total_rate,
        rb,
        rb_rate,
        cv,
        medals,
        medal_mean,
        medal_rate,
        win_rate,
    ]
    df_group = pd.concat(for_concat_list, axis=1)
    df_group = df_group.reset_index()
    return df_group

supabase = get_supabase_client()
query = (
    supabase.table("result_joined")
    .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
)
res = query.execute()
st.write("res.data (first 5):", res.data[:5])
# エラー情報があれば
if hasattr(res, "error"):
    st.write("res.error:", res.error)

df = pd.DataFrame(res.data)
# st.write("df.columns:", df.columns.tolist())

starttime = time.time()

VIEW = "result_joined"
ALL = "すべて表示"

title = "test_page"
st.set_page_config(page_title=title, layout="wide")
st.subheader("テストページ")
# --- page_config ---

# fetch latest
df_latest = fetch_latest(VIEW)
# st.dataframe(df_latest)
# halls = sorted(df_latest["hall"].unique().tolist()) + [ALL]
# models = sorted(df_latest["model"].unique().tolist()) + [ALL]
# models = df_latest["model"].value_counts().index.tolist() + [ALL]
day_last_list = [i for i in range(10)] + [ALL]

# --- 日付処理 ---
n_m_ago_first, n_d_ago, yesterday, today = begin_of_month_to_end_of_month(
    months=3, past_n_days=5
)
ss = st.session_state
ss.setdefault("start_date", n_m_ago_first)
ss.setdefault("end_date", yesterday)

# filter
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    start = st.date_input("start", n_m_ago_first)
with col2:
    end = st.date_input("end", yesterday)
with col3:
    day_last = st.selectbox("day_last", day_last_list)
    if day_last == ALL:
        df = fetch(VIEW, start, end, hall=None, model=None, day_last=None)
    else:
        df = fetch(VIEW, start, end, hall=None, model=None, day_last=day_last)
    df = df.set_index(["hall", "model", "unit_no"])
    df_latest = df_latest.set_index(["hall", "model", "unit_no"])
    safe_index = df.index.intersection(df_latest.index)
    df = df.loc[safe_index].reset_index()
with col4:
    halls = sorted(df["hall"].unique().tolist()) + [ALL]
    halls = sorted(fetch_halls()["name"].tolist()) + [ALL]
    hall = st.selectbox("hall", halls)
    df_hall = df if hall == ALL else df[df["hall"] == hall]
with col5:
    models = [ALL] + sorted(df_hall["model"].unique().tolist())
    model = st.selectbox("model", models)
    df_model = df_hall if model == ALL else df_hall[df_hall["model"] == model]

win_rate = st.slider("勝率を選択", 0.0, 1.0, 0.51)

# supabase
# if hall == ALL and model == ALL:
#     df = fetch(VIEW, start, end, hall=None, model=None, day_last=day_last)
# elif hall == ALL and model != ALL:
#     df = fetch(VIEW, start, end, hall=None, model=model, day_last=day_last)
# elif hall != ALL and model == ALL:
#     df = fetch(VIEW, start, end, hall=hall, model=None, day_last=day_last)
# else:
#     df = fetch(VIEW, start, end, hall=hall, model=model, day_last=day_last)

# 最新設置状態のみにフィルター
# df = df.set_index(["hall", "model", "unit_no"])
# df_latest = df_latest.set_index(["hall", "model", "unit_no"])
# safe_index = df.index.intersection(df_latest.index)
# df = df.loc[safe_index].reset_index()


# Groupe処理
df_pre = pre_process_first(df_model, is_win=1.03)
df_pre = df_pre.drop_duplicates()
group_targets = ["hall", "model", "unit_no", "day_last"]
df_groupe = pre_process_groupe(df_pre, group_targets)
df_groupe_pre = df_groupe[
    (df_groupe["game_m"] >= 3000)
    & (df_groupe["medal_m"] >= 500)
    & (df_groupe["count"] >= 3)
    & (df_groupe["win_rate"] >= win_rate)
]
# df_groupe = df_groupe[df_groupe["win_rate"] >= win_rate]
df_groupe_sort = df_groupe_pre.sort_values("rb_rate")

show_col = [
    "day_last",
    "hall",
    "model",
    "unit_no",
    "count",
    "win_rate",
    "cv",
    "rb_rate",
    "total_rate",
    "game_m",
    "medal_m",
    "medal_rate",
]

show_df = df_groupe_sort[show_col]

st.dataframe(show_df, height="auto", width="stretch", hide_index=True)
st.text(len(show_df))


# --- 詳細データの表示 ---
st.subheader("詳細データ", divider="rainbow")

if hall == ALL:
    st.markdown(
        """
        - ホールまたは末尾日で「全データ」を選択しているため、詳細データは表示していません。
        - 個別のホール・末尾日を選択してください。
        """
    )
elif len(df_groupe_sort) == 0:
    st.markdown("該当データが存在しません。")
else:
    models = df_groupe_sort["model"].unique().tolist()
    units = df_groupe_sort["unit_no"].unique().tolist()
    unit = st.selectbox(f"{len(units)} 件の中から台番号を選択", units)

    df_detail_hall = df_pre[(df_pre["hall"] == hall) & (df_pre["day_last"] == day_last)]
    df_detail_model = df_detail_hall[df_detail_hall["model"].isin(models)]
    df_unit = df_detail_model[df_detail_model["unit_no"] == unit]
    df_unit = df_unit.drop_duplicates()
    show_df = df_unit

    show_cols = [
        "hall",
        "model",
        "unit_no",
        "date",
        "game",
        "medal",
        # "medal_rate",
        "bb",
        "rb",
        "bb_rate",
        "rb_rate",
        # "weekday",
        "total_rate",
        # "is_win",
        # "day",
        # "day_last",
    ]
    st.dataframe(show_df[show_cols], height="auto", hide_index=True, width="stretch")
    
endtime = time.time()
time_diff = endtime - starttime
st.text(f"{time_diff:.03f}")
