import datetime
import streamlit as st

from config.dates import n_days_ago, yesterday
from ui.components import home_link
from ui.filters import filters
from fetch_functions import fetch_results_by_units

PAST_N_DAYS = 5

home_link(position="left")

st.markdown('<a id="page_top"></a>', unsafe_allow_html=True)

# --- page_config ---
page_title = "データベース検索"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

# --- Title etc. ---
# st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
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

ss = st.session_state
ss.setdefault("start_date", n_days_ago(PAST_N_DAYS))
ss.setdefault("end_date", yesterday)

# -- フィルター設定 ---
fi = filters(
    state_prefix="page_a",
    start_date_default = n_days_ago(5),
    visible_fields={
        "pref",
        "hall",
        "model",
        "unit_no",
        "day_last_list",
        "weekday_int_list",
        "start_date",
        "end_date",
    },
)

df = fetch_results_by_units(
    fi["start_date"],
    fi["end_date"],
    day_last=fi["day_last_list"],
    weekday=fi["weekday_int_list"],
    pref=fi["pref"],
    hall=fi["hall"],
    model=fi["model"],
    unit_no=fi["unit_no"],
)
if not df.empty:
    df = df.sort_values("date", ascending=False)

df_sum = df.sum().to_dict()
bb_rate = df_sum["game"] / df_sum["bb"] if df_sum["bb"] != 0 else None
rb_rate = df_sum["game"] / df_sum["rb"] if df_sum["rb"] != 0 else None
bbrb_total = df_sum["bb"] + df_sum["rb"]
total_rate = df_sum["game"] / bbrb_total if bbrb_total != 0 else None

# --- Display ---
st.subheader("検索結果", divider="rainbow", help=help_text)

if df.empty:
    st.text(f"データが存在しません。検索条件の見直しをしてください。")
else:
    show_cols = ["model", "date", "unit_no", "game", "medal", "bb", "rb"]
    show_df = df[show_cols]
    st.text(f"{show_df.shape[0]} 件のデータが存在します。")
    st.dataframe(show_df, height="auto", width="stretch", hide_index=True)

# トップに戻るリンク
home_link(position="right")




# df = fetch_results_by_units(
#     fi["start_date"],
#     fi["end_date"],
#     day_last=fi["day_last_list"],
#     weekday=fi["weekday_int_list"],
#     pref=fi["pref"],
#     hall=fi["hall"],
#     model=fi["model"],
#     unit_no=fi["unit_no"],
# )

# st.dataframe(df, height="auto", width="stretch", hide_index=True)