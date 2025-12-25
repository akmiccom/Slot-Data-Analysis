from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt

from fetch_functions import get_supabase_client, _fetch_all_rows

# from utils import validate_dates
from utils import calc_grape_rate, predict_setting, continuous_setting
from utils import auto_height, make_style_val
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units
from utils import validate_dates, rotate_list_by_today


INTIAL_PERIOD = 3

column_config = {
    "date": st.column_config.DateColumn(width=80),
    "hall": st.column_config.Column(width=150),
    "model": st.column_config.Column(width=70),
    "day_last": st.column_config.NumberColumn(width=30),
    "count": st.column_config.NumberColumn(width=30),
    "unit_no": st.column_config.NumberColumn(width=60),
    "rb_rate": st.column_config.NumberColumn(width=50),
    "medal_rate": st.column_config.NumberColumn(width=50),
    "win_rate": st.column_config.NumberColumn(width=50),
    "avg_madal": st.column_config.NumberColumn(width=50),
    "avg_game": st.column_config.NumberColumn(width=50),
    "pred_setting": st.column_config.NumberColumn(width=50),
    "game": st.column_config.NumberColumn(width=50),
    "medal": st.column_config.NumberColumn(width=50),
    "bb": st.column_config.NumberColumn(width=30),
    "rb": st.column_config.NumberColumn(width=30),
    "weight_setting": st.column_config.NumberColumn(width=30),
    "grape_rate": st.column_config.NumberColumn(width=30),
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
page_title = "台番号別の履歴データ"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader(page_title, divider="rainbow")
st.markdown(
    """
    ページの使い方説明
            """
)


# # --- fetch ---
# @st.cache_data
# def fetch(start_date, end_date, pref=None, hall=None, model=None):
#     ALL = "すべて"
#     supabase = get_supabase_client()
#     query = supabase.table("latest_units_results").select("*")
#     query = query.gte("date", start_date)
#     query = query.lte("date", end_date)
#     if pref not in (None, ALL):
#         query = query.eq("prefecture", pref)
#     if hall not in (None, ALL):
#         # query = query.eq("hall", hall)
#         query = query.in_("hall", [hall])
#     if model not in (None, ALL):
#         # query = query.eq("model", model)
#         query = query.in_("model", [model])
#     rows = _fetch_all_rows(query)
#     df = pd.DataFrame(rows)
#     return df


today = date.today()
n_d_ago = today - timedelta(days=INTIAL_PERIOD)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", today)


st.subheader("ホール別履歴")
col1, col2, col3 = st.columns([1, 2, 2])
with col1:
    prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
    pref = st.selectbox("都道府県", prefectures)
with col2:
    halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
    hall = st.selectbox("halls", halls)
with col3:
    models = fetch_models(pref=pref, hall=hall)
    model = st.selectbox("models", models)

col5, col6, col7, col8 = st.columns(4)
with col5:
    start_date = st.date_input(
        "検索開始日", key="start_date", max_value=today, on_change=validate_dates
    )
with col6:
    end_date = st.date_input(
        "検索終了日", key="end_date", max_value=today, on_change=validate_dates
    )
with col7:
    ALL = "すべて"
    day_lasts = [ALL] + rotate_list_by_today([i for i in range(10)])
    day_last = st.selectbox("末尾日", day_lasts)
with col8:
    WEEKDAY_JA = ["日曜日", "月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日"]
    WEEKDAY_JA_TO_INT = {ja: i for i, ja in enumerate(WEEKDAY_JA)}
    weekdays = [ALL] + WEEKDAY_JA
    weekday_ja = st.selectbox("曜日", weekdays)
    weekday = WEEKDAY_JA_TO_INT[weekday_ja] if weekday_ja != ALL else ALL


tab1, tab2 = st.tabs(["一覧表示", "個別表示"])
with tab1:
    # --- hall history ---
    df = fetch_results_by_units(start_date, end_date, day_last, weekday, pref)
    if df.empty:
        st.write("該当データがありません。")
        st.stop()

    idx = ["hall"]
    # vals = ["game", "medal", "bb", "rb"]
    vals = ["game", "medal"]
    cols = ["date"]
    func = "mean"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.round(0)
    pt = pt.swaplevel(0, 1, axis=1)
    pt_hall = pt

    # --- model history ---
    df = fetch_results_by_units(start_date, end_date, day_last, weekday, pref, hall)
    if df.empty:
        st.write("該当データがありません。")
        st.stop()
    df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d (%a)")

    df = calc_grape_rate(df)
    df["weight_setting"] = df.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    )
    df["weight_setting"] = pd.to_numeric(df["weight_setting"], errors="coerce").round(1)
    idx = ["hall", "model"]
    # vals = ["game", "medal", "bb", "rb", "grape_rate", "weight_setting"]
    vals = ["game", "medal", "weight_setting"]
    cols = ["date"]
    func = "mean"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.round(1)
    pt = pt.swaplevel(0, 1, axis=1)
    pt_model = pt

    # --- unit history ---
    df = fetch_results_by_units(
        start_date, end_date, day_last, weekday, pref, hall, model
    )
    if df.empty:
        st.write("該当データがありません。")
        st.stop()
    # if day_last is not ALL:
    #     df = df[df["day_last"] == day_last]
    df = df.sort_values(["date", "unit_no"], ascending=[False, True])
    df = calc_grape_rate(df)
    df["weight_setting"] = df.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    )
    df["weight_setting"] = pd.to_numeric(df["weight_setting"], errors="coerce").round(1)

    idx = ["hall", "model", "unit_no"]
    vals = ["game", "medal", "bb", "rb", "grape_rate", "weight_setting"]
    vals = ["game", "medal", "weight_setting"]
    cols = ["date"]
    func = "sum"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.swaplevel(0, 1, axis=1)
    pt_unit = pt
    
    st.subheader("ホール別履歴")
    if not pt_hall.empty:
        column_config["hall"] = st.column_config.Column(width=140)
        st.dataframe(pt_hall, column_config=column_config)

    # unit_no を昇順でユニーク取得
    units = sorted(df["unit_no"].unique().tolist(), key=lambda x: int(x))
    chunks = chunk_units_balanced(units, chunk_size=10, min_last=5)

    y_min = df["weight_setting"].min() - 0.2
    y_max = df["weight_setting"].max() + 0.2

    st.write("台数:", len(units), " / グラフ数:", len(chunks))

    for idx, unit_chunk in enumerate(chunks, start=1):
        df_chunk = df[df["unit_no"].isin(unit_chunk)].copy()
        # 凡例クリックで絞る（チャンク内だけなので表示しきれる）
        sel = alt.selection_point(fields=["unit_no"], bind="legend", toggle=True)
        # 高さ：固定がおすすめ（縦に増えるので、1枚あたりは一定が見やすい）
        height = 380

        line = (
            alt.Chart(df_chunk)
            .mark_line(
                strokeWidth=0.2,  # ← 線を細く
                point=alt.MarkConfig(
                    size=120, filled=False  # ← 点を大きく  # 塗りつぶし
                ),
            )
            # .mark_line(point=True)
            # .mark_circle(size=120, opacity=0.8)
            .encode(
                x=alt.X("date:O", title="日付"),
                y=alt.Y(
                    "weight_setting:Q",
                    title="weight_setting",
                    axis=alt.Axis(tickMinStep=1, format=".1f"),
                    scale=alt.Scale(domain=[1, 6]),
                ),
                color=alt.Color(
                    "unit_no:N",
                    legend=alt.Legend(title=f"unit_no（{idx}/{len(chunks)}）"),
                ),
                opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
                tooltip=["date", "model", "unit_no", "game", "medal", "weight_setting"],
            )
            .add_params(sel)
            .properties(
                height=height,
                title=f"{start_date}-{end_date}, {hall}, {model} 設定予測値（{idx}/{len(chunks)}）",
            )
        )
        st.altair_chart(line)

    st.subheader("台番号別履歴")
    if not pt_unit.empty:
        column_config = {
            "hall": st.column_config.Column(width=40),
            "model": st.column_config.Column(width=40),
            "unit_no": st.column_config.NumberColumn(width=60),
            "game": st.column_config.NumberColumn(width=40),
            "medal": st.column_config.NumberColumn(width=40),
            "bb": st.column_config.NumberColumn(width=20),
            "rb": st.column_config.NumberColumn(width=20),
            "weight_setting": st.column_config.NumberColumn(width=30),
            "grape_rate": st.column_config.NumberColumn(width=30),
        }
        st.dataframe(pt_unit, column_config=column_config)
    st.subheader("モデル別履歴")
    if not pt_model.empty:
        column_config["hall"] = st.column_config.Column(width=50)
        column_config["model"] = st.column_config.Column(width=90)
        st.dataframe(pt_model, column_config=column_config)


with tab2:
    column_config["hall"] = st.column_config.Column(width=40)
    column_config["model"] = st.column_config.Column(width=40)
    column_config["unit_no"] = st.column_config.NumberColumn(width=70)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("予測設定の履歴", divider="rainbow")
    with col2:
        value_list = [3, 4, 5]
        threshold_value = st.pills(
            "設定予測値を選択", value_list, default=value_list[1]
        )
        pivot = df.pivot_table(
            index=["hall", "model", "unit_no"],
            columns=["date"],
            values=["weight_setting"],
        )
        pivot = pivot.iloc[:, ::-1]
        style_func = make_style_val(threshold_value)
        num_cols = pivot.select_dtypes(include="number").columns
        df_styled = pivot.style.map(style_func, subset=num_cols).format(
            {col: "{:.1f}" for col in num_cols}
        )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("回転数の履歴", divider="rainbow")
        value_list = [3000, 4000, 5000, 6000]
    with col2:
        threshold_value = st.pills("回転数を選択", value_list, default=value_list[1])
    pivot = df.pivot_table(
        index=["hall", "model", "unit_no"], columns=["date"], values=["game"]
    )
    pivot = pivot.iloc[:, ::-1]
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("出玉数の履歴", divider="rainbow")
        value_list = [0, 100, 200, 300, 500]
    with col2:
        threshold_value = st.pills("出玉数を選択", value_list, default=value_list[1])
    pivot = df.pivot_table(
        index=["hall", "model", "unit_no"], columns=["date"], values=["medal"]
    )
    pivot = pivot.iloc[:, ::-1]
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )


# st.dataframe(df)

# n = df.unit_no.nunique()
# st.write(n)

# if n <= 20:
#     height = 500
# else:
#     height = n * 30

# sel = alt.selection_point(fields=["unit_no"], bind="legend", toggle=True)

# y_min = df["weight_setting"].min() - 0.2
# y_max = df["weight_setting"].max() + 0.2

# line = (
#     alt.Chart(df)
#     .mark_line(point=True)
#     # .mark_circle(size=120, opacity=0.8)
#     .encode(
#         x=alt.X("date", title="日付"),
#         y=alt.Y(
#             "weight_setting:Q",
#             title="wight_setting",
#             axis=alt.Axis(tickMinStep=0.5, format=".1f"),
#             scale=alt.Scale(domain=[y_min, y_max]),
#         ),
#         color=alt.Color("unit_no:N", legend=alt.Legend(title="unit_no")),
#         opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
#         tooltip=["date", "model", "unit_no", "weight_setting"],
#     )
#     .add_params(sel)
#     .properties(height=height, title=f"{start_date}-{end_date}, {hall}, {model} 設定予測値")
# )
# st.altair_chart(line)

# st.subheader("Test")
# pt_model_medal = pt_model.xs("medal", level=1, axis=1)
# st.dataframe(pt_model_medal)
# st.bar_chart(pt_model_medal)