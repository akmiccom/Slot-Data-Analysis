from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
import altair as alt

from fetch_functions import get_supabase_client, _fetch_all_rows
from fetch_functions import fetch_prefectures, fetch_halls
from utils import calc_grape_rate, predict_setting, continuous_setting
from utils import auto_height


def rotate_list_by_today(lst):
    tomorrow_day = date.today().day  # 翌日の「日」
    start = tomorrow_day % len(lst)
    return lst[start:] + lst[:start]


column_config = {
    "date": st.column_config.DateColumn(width=80),
    "hall": st.column_config.Column(width=80),
    "model": st.column_config.Column(width=70),
    "day_last": st.column_config.NumberColumn(width=30),
    "count": st.column_config.NumberColumn(width=30),
    "unit_no": st.column_config.NumberColumn(width=60),
    "rb_rate": st.column_config.NumberColumn(width=50),
    "medal_rate": st.column_config.NumberColumn(width=50),
    "win_rate": st.column_config.NumberColumn(width=50),
    "avg_madal": st.column_config.NumberColumn(width=50),
    "avg_game": st.column_config.NumberColumn(width=50),
    "grape_rate": st.column_config.NumberColumn(width=50),
    "weight_setting": st.column_config.NumberColumn(width=50),
    "pred_setting": st.column_config.NumberColumn(width=50),
    "bb": st.column_config.NumberColumn(width=30),
    "rb": st.column_config.NumberColumn(width=30),
}


# --- title ---
page_title = "台番号別の統計データ"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader(page_title, divider="rainbow")
st.markdown(
    """
    ページの使い方説明
            """
)


# --- fetch ---
supabase = get_supabase_client()


@st.cache_data
def fetch(day_last, pref=None, hall=None, model=None):
    query = supabase.table("medal_rate_by_unit_no").select("*")
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    if model not in (None, ALL):
        query = query.eq("model", model)
    if day_last is not None and day_last != ALL:
        query = query.eq("day_last", day_last)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    return df


@st.cache_data
def fetch_filter(day_last, pref=None, hall=None, count=5, rb_rate=322, win_rate=0.5):
    ALL = "すべて"
    query = supabase.table("medal_rate_by_unit_no").select(
        "day_last,count,hall,prefecture,rb_rate,win_rate"
    )
    if day_last is not None and day_last != ALL:
        query = query.eq("day_last", day_last)
    query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    query = query.gte("count", count)
    query = query.lte("rb_rate", rb_rate)
    query = query.gte("win_rate", win_rate)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    return df


count = st.sidebar.slider("count", 1, 10, 5, 1)
rb_rate = st.sidebar.slider("rb_rate", 250, 400, 320, 20)
win_rate = st.sidebar.slider("win_rate", 0.0, 1.0, 0.5, 0.1)
weight_setting = st.sidebar.slider("weight_setting", 1.0, 6.0, 4.0, 0.5)
# st.dataframe(df)


# --- selecter ---
st.subheader("フィルター", divider="rainbow")
ALL = "すべて"

col6, col7, col8 = st.columns(3)
with col6:
    # query = supabase.table("prefectures").select("name")
    # rows = _fetch_all_rows(query)
    # prefectures = [row["name"] for row in rows]
    prefectures = fetch_prefectures()
    pref = st.selectbox("都道府県を選択", prefectures)

with col7:
    day_lasts = rotate_list_by_today([i for i in range(10)]) + [ALL]
    day_last = st.selectbox("day_last", day_lasts)
    df = fetch_filter(
        day_last, pref="東京都", hall=None, count=count, rb_rate=rb_rate, win_rate=win_rate
    )
# st.text(len(df))

with col8:
    halls = df["hall"].value_counts().index.tolist() + [ALL]
    hall = st.selectbox("hall", halls)


# --- preprocess ---
df = fetch(day_last, pref=pref, hall=hall)
round_list = [
    "bb_rate",
    "rb_rate",
    "total_rate",
    "medal_rate",
    "avg_game",
    "avg_medal",
]
df[round_list] = df[round_list].round(0)
df["win_rate"] = df["win_rate"].round(2)
# df = df[df["avg_game"] >= avg_game]
# df = df[df["avg_medal"] >= avg_medal]
# df = df[df["medal_rate"] >= medal_rate]
df = df[df["win_rate"] >= win_rate]
df = df[df["count"] >= count]
df = df[df["rb_rate"] <= rb_rate]
# st.dataframe(df)

df = df.rename(
    columns={
        "sum_game": "game",
        "sum_medal": "medal",
        "sum_bb": "bb",
        "sum_rb": "rb",
    }
)
df = calc_grape_rate(df)
# df["grape_rate"] = df["grape_rate"].astype(float).round(2)
df["grape_rate"] = pd.to_numeric(df["grape_rate"], errors="coerce").round(2)
df["weight_setting"] = df.apply(
    lambda r: continuous_setting(
        r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
    ),
    axis=1,
).round(1)
df["pred_setting"] = df.apply(
    lambda row: predict_setting(
        row["game"], row["rb"], row["bb"], row["grape_rate"], row["model"]
    )[0],
    axis=1,
)

df = df[df["weight_setting"] >= weight_setting]

# with col8:
#     halls = df["hall"].value_counts().index.tolist() + [ALL]
#     hall = st.selectbox("hall", halls)
#     if hall not in (None, ALL):
#         df = df[df["hall"] == hall]


# --- display ---
st.subheader("検索結果", divider="rainbow")
df_show = df

hall_counts = df_show["hall"].value_counts()
df_show["hall_count"] = df_show["hall"].map(hall_counts)
df_show = df_show.sort_values(
    ["hall", "weight_setting", "model"], ascending=[True, False, True]
)
df_show = df_show.drop(columns="hall_count")

show_cols = [
    "count",
    "hall",
    "model",
    "unit_no",
    "medal_rate",
    "win_rate",
    "pred_setting",
    "weight_setting",
    # "rb_rate",
    # "avg_medal",
    # "avg_game",
    "grape_rate",
]
if day_last == ALL:
    show_cols.insert(0, "day_last")
# df_show = df_show
df_show = df_show[show_cols]

if len(df_show):
    st.markdown(
        f"末尾 **{day_last}** の日の「 **{hall}** 」ついて、**{len(df)}** 件が該当しました。"
    )
    st.dataframe(
        df_show,
        height=auto_height(df_show),
        hide_index=True,
        column_config=column_config,
    )
else:
    st.markdown(
        f"末尾「 **{day_last}** 」の日の「 **{hall}** 」ついて、該当するデータは存在しません。"
    )


# --- display detail ---
@st.cache_data
def fetch_detail(hall, unit_no, day_last_list, period=3):
    today = date.today()
    start_date = date(today.year, today.month, 1) - relativedelta(months=period)
    query = (
        supabase.table("latest_units_results")
        .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
        .in_("day_last", day_last_list)
        .eq("hall", hall)
        .eq("unit_no", unit_no)
        .gte("date", start_date)
        .lte("date", today)
    )
    rows = _fetch_all_rows(query)
    df_detail = pd.DataFrame(rows)
    return df_detail


if day_last == ALL or hall == ALL:
    st.markdown(
        f"""
        - 末尾日・ホール選択で「すべて表示」を選択しているため、詳細データは表示していません。
        - 個別のホール・末尾日を選択してください。
        """
    )
elif len(df):
    st.subheader("履歴データ", divider="rainbow")
    units = df_show["unit_no"].tolist()
    col1, col2, col3 = st.columns(3)
    with col1:
        unit_no = st.selectbox(f"{len(units)} 件の中から台番号を選択", units)
    with col2:
        prev_on = st.toggle("前日のデータを表示する", value=False)
    day_last_list = [day_last]
    if prev_on:
        prev = (day_last - 1) % 10
        day_last_list = [day_last, prev]

    df_detail = fetch_detail(hall, unit_no, day_last_list, period=3)

    if prev_on:
        st.markdown(f"前日と合わせて **{len(df_detail)}** 件を表示しています。")
    else:
        st.markdown(
            f"**{len(df_detail)}** 件を表示しています。3000回転以下の台は設定予測はしていません。"
        )

    # --- preprocess ---
    df_detail["bb_rate"] = (df_detail["game"] / df_detail["bb"]).round(0)
    df_detail["rb_rate"] = (df_detail["game"] / df_detail["rb"]).round(0)
    df_detail = calc_grape_rate(df_detail)
    df["grape_rate"] = pd.to_numeric(df["grape_rate"], errors="coerce").round(2)
    df_detail["weight_setting"] = df_detail.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    ).round(2)
    df_detail["pred_setting"] = df_detail.apply(
        lambda row: predict_setting(
            row["game"], row["rb"], row["bb"], row["grape_rate"], row["model"]
        )[0],
        axis=1,
    )

    df_detail = df_detail.sort_values("date", ascending=False)
    df_detail = df_detail.drop(columns="day_last")

    # --- display ----
    tab1, tab2 = st.tabs(["graph", "dataframe"])
    # --- dataframe ---
    with tab2:
        detail_show_cols = [
            "date",
            "hall",
            "model",
            "unit_no",
            "pred_setting",
            "weight_setting",
            "game",
            "medal",
            "bb",
            "rb",
            "bb_rate",
            "rb_rate",
            "grape_rate",
        ]
        df_show = df_detail[detail_show_cols]
        # df_show = df_detail
        st.dataframe(
            df_show,
            height=auto_height(df_show),
            hide_index=True,
            column_config=column_config,
        )

    with tab1:
        # --- graph ---
        df_show["date"] = pd.to_datetime(df_show["date"])
        df_show["date_str"] = df_show["date"].dt.strftime("%m-%d")

        chart_scatter = (
            alt.Chart(df_show)
            .mark_circle(size=80)
            .encode(
                x=alt.X("date_str:N", title="Date"),
                y=alt.Y(
                    "weight_setting:Q",
                    scale=alt.Scale(domain=[1, 6]),
                ),
                tooltip=["date", "weight_setting", "game"],
            )
        )
        #  Game 数の棒グラフ
        chart_bar = (
            alt.Chart(df_show)
            .mark_bar(opacity=0.3, color="orange")  # ← 半透明で重ねる
            .encode(
                x=alt.X("date_str:N"),
                y=alt.Y("game:Q", title="Game Count"),
            )
        )
        # 日付ごとの縦線（tick ではなくルール）
        chart_lines = (
            alt.Chart(df_show)
            .mark_rule(color="#444444", strokeWidth=1)
            .encode(
                x="date_str:N",
            )
        )
        # chart = chart_lines + chart_bar + chart_scatter
        chart = alt.layer(
            # chart_bar,  # 背景の棒
            chart_lines,  # 補助線
            chart_scatter,  # 散布図（最前面）
        )
        st.altair_chart(chart)

    st.markdown(
        """
        ##### weight_setting, pred_setting の違い
        - 設定の"高さ指標"、集計なら → weight_setting を見る
        - 設定を当てる（1つ選ぶ）なら pred_setting（整数）を見る
        """
    )
