import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from utils_for_streamlit import HALLS, WEEKDAY_MAP
from data_from_supabase import fetch


def pre_process_first(df, is_win=1.03):
    """データに必要な列を追加する"""
    df["date"] = pd.to_datetime(df["date"])
    df["weekday"] = df["date"].dt.day_name()
    df["BB_rate"] = (df["game"] / df["bb"]).round(1)
    df["RB_rate"] = (df["game"] / df["rb"]).round(1)
    df["Total_rate"] = (df["game"] / (df["bb"] + df["rb"])).round(1)
    df["medal_rate"] = ((df["game"] * 3 + df["medal"]) / (df["game"] * 3)).round(3)
    df["is_win"] = df["medal_rate"] > is_win
    df["day"] = df["date"].dt.day
    df["day_last"] = df["day"].astype(str).str[-1].astype(int)
    return df


def pre_process_groupe(df, group_targets):
    grouped = df.groupby(group_targets)
    #
    unit_count = grouped["game"].count()
    unit_count.name = "count"
    #
    is_win = grouped["is_win"].sum()
    win_rate = (is_win / unit_count).round(2)
    win_rate.name = "win_rate"

    game_sum = grouped["game"].sum()
    game_mean = grouped["game"].mean().round(1)
    game_mean.name = "game_m"
    game_std = grouped["game"].std().round(1)
    game_std.name = "game_std"

    medals = grouped["medal"].sum()
    medals_mean = grouped["medal"].mean().round(1)
    medals_mean.name = "medals_m"
    medals_std = grouped["medal"].std().round(1)
    medals_std.name = "medals_std"

    rb = grouped["rb"].sum()
    rb_rate = (game_sum / rb).round(1)
    rb_rate.name = "rb_rate"

    rb_rate_std = grouped["rb"].std().round(1)
    rb_rate_std.name = "rb_rate_std"

    cv = (grouped["rb"].std() / grouped["rb"].mean()).round(3)
    cv.name = "cv"

    bb = grouped["bb"].sum()
    bb_rate = (game_sum / bb).round(1)
    bb_rate.name = "bb_rate"

    medal_rate = ((game_sum * 3 + medals) / (game_sum * 3)).round(3)
    medal_rate.name = "medal_rate"

    for_concat_list = [
        game_sum,
        game_mean,
        unit_count,
        bb,
        bb_rate,
        rb,
        rb_rate,
        cv,
        medals,
        medals_mean,
        medal_rate,
        win_rate,
    ]
    df_day_last = pd.concat(for_concat_list, axis=1)
    df_day_last = df_day_last.reset_index()
    return df_day_last


title = "末尾日統計"
st.set_page_config(page_title=title, layout="wide")
st.title(title)

st.subheader("以下の条件でデータを表示", divider="rainbow")
st.markdown(
    """
    - 回転数 5,000G以上
    - 勝率 50%以上
    - メダル数 +500枚以上
    - 右のタブより、ホール・末尾日で絞り込みしてください。
    """
)


# --- 日付処理 ---
def validate_dates():
    if ss.end_date < ss.start_date:
        ss.start_date = ss.end_date


def begin_of_month_to_end_of_month(months=1, days=1):
    """期間を開始日を指定月数の1日から、n月前の月末からm日まで"""
    year, month = date.today().year, date.today().month
    this_month_first = date(year, month, 1)
    end_date = this_month_first - timedelta(days=days)
    start_date = this_month_first - relativedelta(months=months)

    return start_date, end_date


# --- 表示処理 ---
def adjust_height(df, hall, day):
    """--- 表示高さ自動調整関数 ---"""
    rows = len(df)
    row_height = 30  # 1行あたりの高さ（目安）
    base_height = 100  # ヘッダ・余白ぶん
    max_height = 800  # 上限（スクロール防止）
    height = min(base_height + rows * row_height, max_height)
    if day == "ALL" or hall == "ALL":
        return "auto"
    else:
        return height


# 最新の設置状態を取得してインデックスを取得
def make_df_latest(past_n_days=3):
    today = date.today()
    n_d_ago = today - timedelta(days=past_n_days)
    yesterday = today - timedelta(days=1)
    # df_latest = fetch(HALLS, n_d_ago, yesterday, model_pattern="ジャグラー")
    df_latest = fetch("result_joined", n_d_ago, yesterday, hall=None, model=None)
    df_latest = df_latest.set_index(["hall", "model", "unit_no"])
    return df_latest

df_latest = make_df_latest()

# 日付カラム
start_date, end_date = begin_of_month_to_end_of_month(months=1, days=1)
ss = st.session_state
ss.setdefault("start_date", start_date)
ss.setdefault("end_date", end_date)

# st.text(start_date)
# st.text(end_date)

col1, col2, col3 = st.columns(3)
with col1:
    st.date_input(
        "検索開始日",
        key="start_date",
        value=ss["start_date"],
        max_value=end_date,
        on_change=validate_dates,
    )
with col2:
    st.date_input(
        "検索終了日",
        key="end_date",
        value=ss["end_date"],
        # min_value=ss["start_date"],
        max_value=end_date,
        on_change=validate_dates,
    )


# df読み込んで、最新の設置状態に絞り込み
# df = fetch(HALLS, ss.start_date, ss.end_date, model_pattern="ジャグラー")
df = fetch("result_joined", ss.start_date, ss.end_date, hall=None, model=None)

df = df.set_index(["hall", "model", "unit_no"])
safe_index = df.index.intersection(df_latest.index)
df = df.loc[safe_index].reset_index()

df = pre_process_first(df, is_win=1.03)
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d-%a")
group_targets = ["hall", "model", "unit_no", "day_last"]
df_groupe = pre_process_groupe(df, group_targets)

# --- 選択用リスト作成 ---
day_list = df_groupe["day_last"].unique().tolist()
display_day = date.today().day + 1
days = day_list[display_day:] + day_list[:display_day]
if len(days) > 6:
    days.insert(6, "ALL")
halls = sorted(df_groupe["hall"].unique().tolist())
if len(halls) > 6:
    halls.insert(6, "ALL")
models = sorted(df_groupe["model"].unique().tolist())
if len(models) > 6:
    models.insert(6, "ALL")

# --- フィルタ ---
st.subheader("フィルタ", divider="rainbow")
col1, col2, col3 = st.columns(3)
with col1:
    day = st.selectbox("末尾日を選択", days)
with col2:
    hall = st.selectbox("ホールを選択", halls)
with col3:
    # model = st.selectbox("ホールを選択", models)
    win_rate = st.slider("勝率範囲を選択", 0.0, 1.0, 0.51)

# --- フィルタリング ---
st.text("今設置されている状態に修正 -> df_groupp.iloc[latest_index]")
df_groupe = df_groupe[df_groupe["game_m"] >= 3000]
df_groupe = df_groupe[df_groupe["count"] >= 3]
df_groupe = df_groupe[df_groupe["win_rate"] >= win_rate]
if hall == "ALL" and day == "ALL":
    filtered = df_groupe
elif hall == "ALL" and day != "ALL":
    filtered = df_groupe[df_groupe["day_last"] == day]
elif hall != "ALL" and day == "ALL":
    filtered = df_groupe[df_groupe["hall"] == hall]
else:
    filtered = df_groupe[
        (df_groupe["hall"] == hall) & (df_groupe["day_last"] == day)
    ]


show_col = [
    "day_last",
    "hall",
    "model",
    "unit_no",
    "win_rate",
    "count",
    # "game",
    "game_m",
    # "medal",
    "medals_m",
    "medal_rate",
    # "bb",
    "bb_rate",
    # "rb",
    "rb_rate",
    "cv",
]

show_df = filtered
show_df = filtered[show_col]
st.subheader("データ表示", divider="rainbow")
height = adjust_height(show_df, hall, day)

if len(show_df) == 0:
    st.markdown("該当データが存在しません。")
else:
    st.write(f"{len(filtered):,} 件を表示")
    st.dataframe(show_df, height=height, hide_index=True)

# --- 詳細データの表示 ---
st.subheader("詳細データ", divider="rainbow")

if hall == "ALL" or day == "ALL":
    st.markdown(
        """
        - ホールまたは末尾日で「全データ」を選択しているため、詳細データは表示していません。
        - 個別のホール・末尾日を選択してください。
        """
    )
elif len(filtered) == 0:
    st.markdown("該当データが存在しません。")
else:
    models = filtered["model"].unique().tolist()
    units = filtered["unit_no"].unique().tolist()
    unit = st.selectbox(f"{len(units)} 件の中から台番号を選択", units)

    # st.dataframe(df)

    hall_df = df[(df["hall"] == hall) & (df["day_last"] == day)]
    model_df = hall_df[hall_df["model"].isin(models)]
    unit_df = model_df[model_df["unit_no"] == unit]

    show_df = unit_df
    show_cols = [
        "hall",
        "model",
        "unit_no",
        "date",
        "game",
        "medal",
        "medal_rate",
        "bb",
        "rb",
        "BB_rate",
        "RB_rate",
        # "weekday",
        "Total_rate",
        # "is_win",
        # "day",
        # "day_last",
    ]
    st.dataframe(show_df[show_cols], height="auto", hide_index=True, width="stretch")
