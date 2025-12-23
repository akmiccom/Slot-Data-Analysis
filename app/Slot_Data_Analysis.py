import pandas as pd
from datetime import date, timedelta
import streamlit as st
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units
from utils import validate_dates


title = "分析データ一覧"
st.set_page_config(page_title=title, layout="wide",
                   initial_sidebar_state="collapsed")

# st.divider()

st.header(title, divider="rainbow")
st.page_link("pages/01_データベース検索.py", label="データベース検索", icon="📊")
st.page_link("pages/98_Statistics_by_Hall.py", label="ホール別の分析データ", icon="📈")
st.page_link("pages/97_Statistics_by_Model.py", label="機種別の分析データ", icon="📈")
st.page_link("pages/96_Statistics_by_Unit.py", label="台番号別の分析データ", icon="📈")
st.page_link("pages/95_History_by_Unit.py", label="台番号別の履歴データ", icon="📈")
st.page_link("pages/94_メダル推移グラフ.py", label="メダル推移グラフ", icon="📈")


# --- Sample ---
st.subheader("最新データ状況", divider="rainbow")

today = date.today()
start = today - timedelta(days=5)
end = today - timedelta(days=1)
tab1, tab2, tab3 = st.tabs(["都道府県一覧", "モデル一覧", "ホール一覧"])
with tab1:
    prefectures = fetch_prefectures()
    st.write(prefectures)
with tab2:
    models = fetch_models()
    st.write(models)
with tab3:
    halls = fetch_halls()
    st.write(halls)

st.subheader("TOP PAGE に乗せるもの", divider="rainbow")
st.markdown(
    f"""
    - ホール一覧
    - ホール分析の月別ダッシュボードを作成
    - 機種別出玉推移
    """
)

st.markdown(
    """
    ## スマホ画面に合わせた設定
    - header : 7文字/行
    - subheader : 8文字/行
    - 箇条書き : 16文字/行
    - 文章 : 20文字/行
    """
)

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