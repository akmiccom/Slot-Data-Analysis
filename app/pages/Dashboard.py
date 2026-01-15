import streamlit as st

from config.constants import KEY_MAP
from config.dates import prev_month_first, initial_day_last
from ui.filters import filters, filters_for_rb_rate
from ui.components import home_link
from ui.charts import charts_on_unit_no, charts_on_all_model
from logic.preprocess import preprocess_for_table, preprocess_for_rb_rate, preprocess

from fetch_functions import fetch_results_by_units


# page_config（必ず最初）
page_title = "Dashboard"
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

fi = filters_for_rb_rate()
# st.write(fi)

prev_month = 3
sel_rows = None
ss = st.session_state

r1c1, r1c2 = st.columns([1, 2], gap="small")

with r1c1:
    # RB_RATE_LIST
    if fi["day_last_list"] is not None or fi["weekday_int_list"] is not None:
        with st.expander(
            f"{fi['model']} , {fi['day_last_list']}のつく日集計",
            expanded=True,
        ):
            df = fetch_results_by_units(
                fi["start_date"],
                fi["end_date"],
                day_last=fi["day_last_list"],
                weekday=fi["weekday_int_list"],
                pref=fi["pref"],
                # hall=None,
                model=fi["model"],
            )
            df_rb_rate = preprocess_for_rb_rate(df)
            event = st.dataframe(
                df_rb_rate,
                width="stretch",
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",  # 選択されたら再実行して event が更新される
            )
            sel_rows = event.selection.get("rows", [])

            if sel_rows:
                row = df_rb_rate.iloc[sel_rows[0]]
                ss["selected_unit"] = {
                    "hall": row["hall"],
                    "model": fi["model"],
                    "unit_no": int(row["unit_no"]),
                    "start_date": fi["start_date"],
                    "end_date": fi["end_date"],
                    "pref": fi["pref"],
                    "day_last_list": fi["day_last_list"],
                    "weekday_int_list": fi["weekday_int_list"],
                }
            # else:
            #     st.write()
    else:
        # st.write("曜日もしくは末尾日を選択してください")
        st.stop()

selected = ss.get("selected_unit")

with r1c2:
    # if not sel_rows:
    if sel_rows and selected:
        day_last_list = selected["day_last_list"]
        if not selected["day_last_list"]:
            day_last_list = None
        weekday_int_list = selected["weekday_int_list"]
        if not selected["weekday_int_list"]:
            weekday_int_list = None
        # クリックした行の台を表示する
        expander_title = (
            f"{selected['hall']}: {selected['model']}: No.{selected['unit_no']}"
        )
        with st.expander(expander_title, expanded=True):
            df_unit = fetch_results_by_units(
                selected["start_date"],
                selected["end_date"],
                day_last=day_last_list,
                weekday=weekday_int_list,
                pref=selected["pref"],
                hall=selected["hall"],
                model=selected["model"],
                unit_no=selected["unit_no"],
            )
            if df_unit is None or df_unit.empty:
                st.info("選択した台のデータがありません。")
            else:
                chart = charts_on_unit_no(df_unit, selected["model"])
                st.altair_chart(chart, width="stretch")

        with st.expander("詳細テーブル", expanded=False):
            if df_unit is not None and not df_unit.empty:
                df_table = preprocess_for_table(df_unit)
                st.dataframe(df_table, hide_index=True, width="stretch")

    else:
        expander_title = f"RB確率一覧から台を選択してください"
        with st.expander(expander_title, expanded=True):
            st.stop()


home_link(position="right")
