import pandas as pd
import datetime
import streamlit as st
from data_from_supabase import fetch, fetch_halls, fetch_models, fetch_latest
from utils import validate_dates


title = "データ分析"
st.set_page_config(page_title=title, layout="wide",
                   initial_sidebar_state="collapsed")

# st.subheader(title)
st.divider()

st.subheader("分析データ一覧", divider="rainbow")
st.page_link("pages/01_データベース検索.py", label="データベース検索", icon="📊")
st.page_link("pages/98_Statistics_by_Hall.py", label="ホール別の分析データ", icon="📈")
st.page_link("pages/97_Statistics_by_Model.py", label="機種別の分析データ", icon="📈")
st.page_link("pages/96_Statistics_by_Unit.py", label="台番号別の分析データ", icon="📈")
st.page_link("pages/95_History_by_Unit.py", label="台番号別の履歴データ", icon="📈")
# st.page_link("pages/02_ホール別出玉率履歴.py", label="ホール別の分析", icon="📈")
# st.page_link("pages/03_機種別出玉率履歴.py", label="機種別の分析", icon="📈")
# st.page_link("pages/04_台別出玉率履歴.py", label="台番号別の分析", icon="📈")
# st.page_link("pages/05_末尾日統計.py", label="末尾日別の分析", icon="📈")

st.subheader("TOP PAGE に乗せるもの", divider="rainbow")
st.markdown(
    f"""
    - ホール一覧
    - グラフなどでホール分析の月別ダッシュボードを作成
    - 機種別出玉推移
    """
)

# --- Sample ---
st.subheader("最新のホール・モデルの状況", divider="rainbow")
df_latest = fetch_latest("result_joined", hall=None, model=None)
tab1, tab2, tab3 = st.tabs(["ホール別台数", "モデル別台数", "その他"])
with tab1:
    grouped = df_latest.groupby("hall")
    unit_count = grouped["unit_no"].count().sort_values(ascending=False)
    unit_count = pd.DataFrame(unit_count).rename(
        columns={"unit_no": "ホール別ジャグラーの台数"}
    )
    halls = unit_count.index.tolist()
    st.dataframe(unit_count, height="auto", width="content")
with tab2:
    models = fetch_models()
    grouped = df_latest.groupby("model")
    unit_count = grouped["unit_no"].count().sort_values(ascending=False)
    unit_count = pd.DataFrame(unit_count).rename(columns={"unit_no": "機種別の台数"})
    st.dataframe(unit_count, height="auto", width="content")
with tab3:
    ALL = "すべて表示"
    col1, col2 = st.columns(2)
    with col1:
        if len(halls) > 5:
            halls.insert(5, ALL)
        hall = st.selectbox("ホール選択", halls)
        df_hall = df_latest if hall == ALL else df_latest[df_latest["hall"] == hall]
    with col2:
        models = df_hall["model"].value_counts().index.tolist()
        model = st.selectbox("モデル選択", models)
        df_model = df_hall if model == ALL else df_hall[df_hall["model"] == model]

    st.dataframe(df_model)

st.markdown(
    """
    ## スマホ画面に合わせた設定
    - header : 7文字/行
    - subheader : 8文字/行
    - 箇条書き : 16文字/行
    - 文章 : 20文字/行
    """
)