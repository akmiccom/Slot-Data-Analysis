import streamlit as st

from ui.filters import filters_for_rb_rate
from ui.components import home_link
from logic.preprocess import preprocess_for_rb_rate

from fetch_functions import fetch_results_by_units


column_config = {
    "hall": st.column_config.Column(width=140),
}


# page_config（必ず最初）
page_title = "RB確率日別集計"
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

fi = filters_for_rb_rate()


def rb_prob_by_unit(fi):
    sel_rows = None
    ss = st.session_state

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
        st.info("曜日もしくは末尾日を選択してください")
        home_link(position="left")
        st.stop()

    selected = ss.get("selected_unit")
    return sel_rows, selected


sel_rows, selected = rb_prob_by_unit(fi)

st.write(sel_rows)
st.write(selected)

home_link(position="right")
