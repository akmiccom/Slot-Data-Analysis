import os
import streamlit as st

from config.dates import n_days_ago, yesterday
from ui.filters import filters_for_history
from ui.filters import filters
from ui.components import home_link
from ui.charts import charts_on_unit_no

from fetch_functions import fetch_results_by_units
from ui.helpers import order_by_priority
from config.constants import PRIORITY_MODELS


# page_config
page_title = os.path.splitext(os.path.basename(__file__))[0]
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

home_link(position="left")

st.header(page_title)

# --- 日付処理 ---
# today = datetime.date.today()
# n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
# yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_days_ago(5))
ss.setdefault("end_date", yesterday)

# filters
fi = filters(
    state_prefix="page_a",
    start_date_default = n_days_ago(5),
    visible_fields={
        "pref",
        "hall",
        "model",
        "unit_no",
        # "day_last_list",
        # "weekday_int_list",
        "start_date",
        "end_date",
    },
)

c1, c2 = st.columns(2, gap="small")

with c1:
    st.subheader("単日 ✕ 全台", divider="rainbow")
    df = fetch_results_by_units(
        fi["end_date"],
        fi["end_date"],
        pref=fi["pref"],
        hall=fi["hall"],
    )
    if df is None or df.empty:
        st.info("選択した条件のデータがありません。")
        home_link(position="left")
        st.stop()

    models = df["model"].unique().tolist()
    models = order_by_priority(models, PRIORITY_MODELS)

    for model in models:
        df_model = df[df["model"] == model]
        count = df_model["unit_no"].nunique()
        expander_title = f"{fi['hall']}: {model}: {count}台: {fi['end_date']}"
        with st.expander(expander_title, expanded=True):
            charts = charts_on_unit_no(df_model, model, single_day=True)
            st.altair_chart(charts, width="stretch")
    # home_link(position="left")


with c2:
    st.subheader("複数日 ✕ 台番号", divider="rainbow")
    df = fetch_results_by_units(
        fi["start_date"],
        n_days_ago(1),
        pref=fi["pref"],
        hall=fi["hall"],
        model=fi["model"],
        unit_no=fi["unit_no"],
    )

    if df is None or df.empty:
        st.info("台番号を選択してください。")

    else:
        for unit_no in fi["unit_no"]:
            df_unit = df[df["unit_no"] == unit_no]
            if df_unit is None or df_unit.empty:
                st.info(f"台番号 {unit_no} のデータがありません。")
                continue
            else:
                expander_title = f"{fi['hall']}: {fi['model']}: {unit_no}"
                with st.expander(expander_title, expanded=True):
                    charts = charts_on_unit_no(df_unit, fi["model"], single_day=False)
                    st.altair_chart(charts, width="stretch")

    home_link(position="right")
