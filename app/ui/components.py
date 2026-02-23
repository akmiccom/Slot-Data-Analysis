# ui/components.py
import streamlit as st

"""
UI部品はここに集約し、ページ側を短くする
"""


# ホームリンク設置
def home_link(position="right"):
    st.markdown(
        f"""
        <div style="text-align:{position};">
            <a href="/" target="_self" style="text-decoration:none;">🏠 HOME</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

