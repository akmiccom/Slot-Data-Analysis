import datetime
import streamlit as st
from data_from_supabase import fetch, fetch_halls

N_PAST_DAYS = 7
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=N_PAST_DAYS)
yesterday = today - datetime.timedelta(days=1)

title = "スロットデータ分析"
st.set_page_config(page_title=title, layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    ## スマホ画面に合わせた設定
    - header : 7文字/行
    - subheader : 8文字/行
    - 箇条書き : 16文字/行
    - 文章 : 20文字/行
    """
)

st.divider()

st.header(title)
st.subheader("TOP PAGE に乗せるもの", divider="rainbow")
st.markdown(
    f"""
    - ホール一覧
    - グラフなどでホール分析の月別ダッシュボードを作成
    - 機種別出玉推移
    """
)


st.subheader("分析データ一覧", divider="rainbow")
st.page_link("pages/01_データベース検索.py", label="データベース検索", icon="📊")
st.page_link("pages/02_ホール別出玉率履歴.py", label="ホール別の分析", icon="📈")
st.page_link("pages/03_機種別出玉率履歴.py", label="機種別の分析", icon="📈")
st.page_link("pages/04_台別出玉率履歴.py", label="台番号別の分析", icon="📈")
st.page_link("pages/06_末尾日統計.py", label="末尾日別の分析", icon="📈")




st.subheader("Streamlit Widgets Sample", divider="gray")
tab1, tab2, tab3 = st.tabs(["概要", "詳細", "その他"])
with tab1:
    st.markdown("ここには概要を表示します。")
with tab2:
    st.markdown("ここには詳細を表示します。")
with tab3:
    df = fetch("result_joined", n_d_ago, today, hall=None, model=None)
    st.markdown(f"""
        ホール {df.hall.nunique()} 件、モデル {df.model.nunique()} 件, データ {df.shape[0]} 件 を表示しています。
        """)
    df = df.sort_values(by=["date", "hall", "model"], ascending=[False, True, True])
    st.dataframe(df, height="auto", width="stretch")



# --- UI ---
st.header("データ検索")

df = fetch("result_joined", today-datetime.timedelta(days=3), today, hall=None, model=None)
halls = sorted(df.hall.unique().tolist())
models = sorted(df.model.unique().tolist())

start = st.date_input("開始日", n_d_ago)
end = st.date_input("終了日", yesterday)

df = fetch("result_joined", start, end)

halls = sorted(df.hall.unique().tolist())
hall = st.selectbox("ホール", halls)
df_hall = fetch("result_joined", start, end, hall)

models = df_hall["model"].value_counts().index.tolist()
model = st.selectbox("モデル", models)
df_model = fetch("result_joined", start, end, hall, model)

units = sorted(df_model.unit_no.unique().tolist())
unit = st.selectbox("モデル", units)
df_unit = df_model[df_model["unit_no"] == unit]

# if st.button("検索"):
st.write(f"{len(df_unit)} 件の結果")
st.dataframe(df_unit.head(500))
