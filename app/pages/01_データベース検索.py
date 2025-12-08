import streamlit as st
# import pandas as pd
import datetime
from utils import validate_dates
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units


PAST_N_DAYS = 5

st.markdown('<a id="page_top"></a>', unsafe_allow_html=True)

# --- page_config ---
page_title = "データベース検索"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

# --- Title etc. ---
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.header(page_title)
st.markdown(
    """
    - ホール・機種・台番・期間で絞り込みが可能です。
    - ホールごとに台数が多い機種を優先的に表示します。
    - 台番号で「すべて表示」して、日付を一日に絞るとその日のデータを一覧で確認できます。
    """
)

# --- UI ---
help_text = f"過去{PAST_N_DAYS}日間のデータを表示しています。"
st.subheader("フィルター設定", divider="rainbow", help=help_text)

# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

# -- フィルター設定 ---
ALL = "すべて表示"
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    prefectures = fetch_prefectures()
    pref = st.selectbox("都道府県を選択", prefectures)
with col2:
    halls = fetch_halls(pref=pref)
    hall = st.selectbox("ホールを選択", halls, help="お気に入り機能追加??")
with col3:
    models = fetch_models(pref=pref, hall=hall)
    model = st.selectbox("機種を選択", models, help="台数の多い順に表示")
with col4:
    units = fetch_units(pref=pref, hall=hall, model=model)
    unit_no = st.selectbox("台番号を選択", units, help="すべて表示も可能")
with col5:
    start = st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col6:
    end = st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
    df = fetch_results_by_units(start, end, pref, hall, model, unit_no)
    if not df.empty:
        df = df.sort_values("date", ascending=False)

# --- Display ---
st.subheader("検索結果", divider="rainbow", help=help_text)

if df.empty:
    st.text(f"データが存在しません。検索条件の見直しをしてください。")
else:
    st.markdown(
        f"""
        - 📅 検索期間: {ss.start_date} ～ {ss.end_date}
        - 📅 ホール: {df.hall.values[0]}
        - 📅 機種: {df.model.values[0]}
        """
    )
    show_cols = ["model", "date", "unit_no", "game", "medal", "bb", "rb"]
    show_df = df[show_cols]

    st.dataframe(show_df, height="auto", width="stretch", hide_index=True)
    st.text(f"{show_df.shape[0]} 件のデータが存在します。")


# トップに戻るリンク
st.markdown(
    """
    <div style="text-align: right;">
        <a href="/"
           target="_self"
           style="font-size: 16px; text-decoration: none;">
            🏠 HOME
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
