from datetime import date
import pandas as pd
import streamlit as st
import altair as alt

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import calc_grape_rate, predict_setting, continuous_setting
from utils import auto_height


def rotate_list_by_tomorrow(lst):
    tomorrow_day = date.today().day + 1  # 翌日の「日」
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
st.header(page_title, divider="rainbow")
st.markdown(
    """
    ページの使い方説明
            """
)


# --- fetch ---
supabase = get_supabase_client()


@st.cache_data
def fetch(day_last, hall=None, model=None):
    query = supabase.table("medal_rate_by_unit_no").select("*")
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    if model not in (None, ALL):
        query = query.eq("model", model)
    if day_last is not None and day_last != ALL:
        query = query.eq("day_last", day_last)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    return df


# --- selecter ---
st.subheader("フィルター", divider="rainbow")
ALL = "すべて"
col1, col2, col3, col4, col5 = st.columns(5)
col6, col7, col8 = st.columns(3)
with col1:
    count = st.slider("count", 3, 10, 6, 1)
with col2:
    medal_rate = st.slider("medal_rate", 100, 106, 103, 1)
with col3:
    win_rate = st.slider("win_rate", 0.0, 1.0, 0.51, 0.1)
with col4:
    avg_game = st.slider(
        "avg_game", min_value=1000, max_value=5000, value=3000, step=1000
    )
with col5:
    avg_medal = st.slider("avg_medal", 0, 1000, 500, 100)

with col6:
    month_list = ["1month", "2months", "3months"]
    month = st.pills("集計期間を選択(準備中)", month_list, default=month_list[-1])

with col7:
    day_lasts = rotate_list_by_tomorrow([i for i in range(10)]) + [ALL]
    day_last = st.selectbox("day_last", day_lasts)
    # --- preprocess ---
    df = fetch(day_last)
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
    df = df[df["avg_game"] >= avg_game]
    df = df[df["avg_medal"] >= avg_medal]
    df = df[df["medal_rate"] >= medal_rate]
    df = df[df["win_rate"] >= win_rate]
    df = df[df["count"] >= count]
    df = df[df["rb_rate"] <= 322]

with col8:
    halls = df["hall"].value_counts().index.tolist() + [ALL]
    hall = st.selectbox("hall", halls)
    if hall not in (None, ALL):
        df = df[df["hall"] == hall]

df = df.rename(
    columns={"sum_game": "game", "sum_medal": "medal", "sum_bb": "bb", "sum_rb": "rb"}
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

# --- display ---
st.subheader("検索結果", divider="rainbow")
df_show = df

hall_counts = df_show["hall"].value_counts()
df_show["hall_count"] = df_show["hall"].map(hall_counts)
df_show = df_show.sort_values(
    ["hall_count", "hall", "model", "rb_rate"], ascending=[False, True, True, True]
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
def fetch_detail(hall, unit_no, day_last_list):
    query = (
        supabase.table("latest_units_results")
        .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
        .in_("day_last", day_last_list)
        .eq("hall", hall)
        .eq("unit_no", unit_no)
        .gte("date", "2025-08-01")
        .lte("date", "2025-11-25")
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

    df_detail = fetch_detail(hall, unit_no, day_last_list)

    if prev_on:
        st.markdown(f"前日と合わせて **{len(df_detail)}** 件を表示しています。")
    else:
        st.markdown(f"**{len(df_detail)}** 件を表示しています。")

    # --- preprocess ---
    df_detail["bb_rate"] = (df_detail["game"] / df_detail["bb"]).round(0)
    df_detail["rb_rate"] = (df_detail["game"] / df_detail["rb"]).round(0)
    df_detail = calc_grape_rate(df_detail)
    # df_detail["grape_rate"] = df_detail["grape_rate"].astype(float).round(2)
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
        chart = (
            alt.Chart(df_show)
            .mark_line(point=True)  # 点 + ライン
            .encode(
                x="date:T",  # 横軸：日付
                y="weight_setting:Q",  # 縦軸：数値
                tooltip=["date", "weight_setting"],
            )
            .properties(width="container", height=350)
        )
        st.altair_chart(chart, use_container_width=True)

        st.markdown(
            """
            ##### weight_setting, pred_setting の違い
            - 設定の"高さ指標"、集計なら → weight_setting を見る
            - 設定を当てる（1つ選ぶ）なら pred_setting（整数）を見る
            """
        )
