import datetime
import streamlit as st
from data_from_supabase import fetch, fetch_halls
from utils import validate_dates

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

# --- UI ---
st.subheader("データ検索", divider="rainbow")

# --- 日付設定 ---
N_PAST_DAYS = 5
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
n_d_ago = today - datetime.timedelta(days=N_PAST_DAYS)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

# --- 初期読み込み ---
df = fetch("result_joined", n_d_ago, today, hall=None, model=None)

# -- フィルター設定 ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col2:
    st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
with col3:
    halls = sorted(df.hall.unique().tolist())
    hall = st.selectbox("ホール", halls)
    df_hall = fetch("result_joined", ss.start_date, ss.end_date, hall)
with col4:
    models = df_hall["model"].value_counts().index.tolist()
    model = st.selectbox("モデル", models)
    df_model = fetch("result_joined", ss.start_date, ss.end_date, hall, model)
with col5:
    units = sorted(df_model.unit_no.unique().tolist())
    unit = st.selectbox("台番号", units)
    df_unit = df_model[df_model["unit_no"] == unit]

# --- Display ---
st.write(f"{len(df_unit)} 件の結果を表示しています。 (最大表示数50件)")
st.dataframe(df_unit.head(50), height="auto")

# --- Sample ---
st.subheader("Streamlit Widgets Sample", divider="gray")
tab1, tab2, tab3 = st.tabs(["概要", "詳細", "その他"])
with tab1:
    st.markdown("ここには概要を表示します。")
with tab2:
    st.markdown("ここには詳細を表示します。")
with tab3:
    st.markdown("ここにはその他を表示します。")
