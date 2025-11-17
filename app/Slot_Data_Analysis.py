import datetime
import streamlit as st
from data_from_supabase import fetch

N_PAST_DAYS = 3
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=N_PAST_DAYS)
yesterday = today - datetime.timedelta(days=1)

title = "スロットデータ分析"
st.set_page_config(page_title=title, layout="wide", initial_sidebar_state="collapsed")
st.title(title)

st.header("TOP PAGE に乗せるもの", divider="rainbow")
st.markdown(
    f"""
    - グラフなどでホール分析の月別ダッシュボードを作成
    - 機種別出玉推移
    """
)


st.page_link("pages/01_データベース検索.py", label="データベース", icon="📊")
st.page_link("pages/02_ホール別出玉率履歴.py", label="ホール別分析", icon="📈")
st.page_link("pages/03_機種別出玉率履歴.py", label="機別種分析", icon="📈")
st.page_link("pages/04_台別出玉率履歴.py", label="台別分析", icon="📈")
st.page_link("pages/06_末尾日統計.py", label="末尾日分析", icon="📈")


st.subheader("tab 切り替えサンプル", divider="grey")
tab1, tab2 = st.tabs(["概要", "詳細"])
with tab1:
    st.markdown("tab1")
with tab2:
    st.markdown("tab2")

# st.header(f"データベースから最新 {N_PAST_DAYS} 日分のデータを表示", divider="rainbow")
# df = fetch("result_joined", n_d_ago, today, hall=None, model=None)
# df = df.sort_values(by=["date", "hall", "model"], ascending=[False, True, True])
# st.dataframe(df, height="auto", width="stretch")
# st.markdown(f"""
#     ホール {df.hall.nunique()} 件、モデル {df.model.nunique()} 件, データ {df.shape[0]} 件 を表示しています。
#     """)
