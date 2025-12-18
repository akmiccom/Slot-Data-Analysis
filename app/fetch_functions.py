import os
from datetime import date, timedelta
from typing import Optional, Union, Any
import pandas as pd
from supabase import create_client, Client
import streamlit as st


@st.cache_resource
def get_supabase_client() -> Client:
    """supabese のクライアントを取得"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    # key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY が設定されていません。")
    return create_client(url, key)


# --------------------------------------------------
# 内部共通関数：ページングして全部取ってくる
# --------------------------------------------------
def _fetch_all_rows(query, page_size: int = 1000) -> list[dict[str, Any]]:
    """
    Supabase の 1000件制限を回避するための共通関数。
    渡された query に対して range() でページングしながら全件取得する。
    """
    all_rows: list[dict[str, Any]] = []
    page = 0

    while True:
        start_i = page * page_size
        end_i = start_i + page_size - 1
        res = query.range(start_i, end_i).execute()
        rows = res.data
        if not rows:
            break
        all_rows.extend(rows)
        # 取得件数が page_size 未満なら最後まで取り切ったと判断して終了
        if len(rows) < page_size:
            break
        page += 1

    return all_rows


# --------------------------------------------------
# ① 期間指定＆hall/model でフィルタ（既存 fetch の改良版）
# --------------------------------------------------
@st.cache_data
def fetch(
    view: str,
    start: Union[str, date],
    end: Union[str, date],
    hall: Optional[str] = None,
    model: Optional[str] = None,
    day_last: Optional[int] = None,
) -> pd.DataFrame:
    """
    Supabase から date 範囲でデータ取得。
    hall, model を指定しない場合はすべてを取得。
    内部でページングして 1000件制限を回避する。
    """
    supabase = get_supabase_client()
    query = (
        supabase.table(view)
        .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
        .gte("date", start)
        .lte("date", end)
    )
    if hall is not None:
        query = query.eq("hall", hall)
    if model is not None:
        query = query.eq("model", model)
    if day_last is not None:
        query = query.eq("day_last", day_last)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)

    return df


@st.cache_data
def fetch_results_by_units(
    start_date, end_date, day_last=None, weekday=None, pref=None, hall=None, model=None, unit_no=None
) -> pd.DataFrame:
    """
    latest_units_results から、指定期間・指定条件でデータを取得する。
    pref, hall, model, unit_no:
        None or "すべて" の場合はフィルタしない。
    period:
        今日を除いた直近 period 日分を取得する（日数ベース）。
    """
    ALL = "すべて"

    supabase = get_supabase_client()

    # ベースクエリ
    query = (
        supabase.table("latest_units_results")
        .select("*")
        .gte("date", start_date.isoformat())
        .lte("date", end_date.isoformat())
    )
    # 末尾日フィルタ
    if day_last not in (None, ALL):
        query = query.eq("day_last", day_last)
    # 曜日フィルタ
    if weekday not in (None, ALL):
        query = query.eq("weekday", weekday)
    # 都道府県フィルタ
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    # ホールフィルタ
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    # 機種フィルタ
    if model not in (None, ALL):
        query = query.eq("model", model)
    # 台番号フィルタ
    if unit_no not in (None, ALL):
        query = query.eq("unit_no", unit_no)
    # 実行
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    # 対象列がない場合のエラーを避ける
    if df.empty:
        return df

    return df


# --------------------------------------------------
# マスタ系： prefectures / halls / models / units
# --------------------------------------------------
@st.cache_data
def fetch_prefectures():
    supabase = get_supabase_client()
    query = supabase.table("prefectures").select("*").order("prefecture_id")
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    prefectures = [row["name"] for row in rows]
    return prefectures


@st.cache_data
def fetch_halls(pref=None):
    """
    latest_models から、指定した都道府県のホール名一覧を取得する。
    pref が None または "すべて" の場合は都道府県での絞り込みなし。
    戻り値はホール名のリスト。
    """
    ALL = "すべて"
    supabase = get_supabase_client()

    # 必要なカラムだけ取得（通信量削減）
    query = supabase.table("latest_models").select("prefecture, hall")
    # 都道府県フィルタ
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    # 実行
    rows = _fetch_all_rows(query)
    # データがなければ空リスト
    if not rows:
        return []
    df = pd.DataFrame(rows)
    # 念のためカラム存在チェック
    if "hall" not in df.columns:
        return []
    halls = df["hall"].unique().tolist()
    # ユニークなホール名をアルファベット/五十音順で安定ソート
    return halls


@st.cache_data
def fetch_models(pref=None, hall=None):
    ALL = "すべて"
    supabase = get_supabase_client()
    query = supabase.table("latest_models").select("prefecture,hall,model")
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    models = df["model"].unique().tolist()
    return models


@st.cache_data
def fetch_units(pref=None, hall=None, model=None):
    """
    latest_units_per_hall から、指定条件に合うユニット番号一覧を返す。
    pref, hall, model が None または "すべて" の場合はフィルタ無し。
    戻り値はユニット番号のリスト。
    """
    ALL = "すべて"
    supabase = get_supabase_client()
    # ベースクエリ
    query = supabase.table("latest_units_per_hall").select(
        "unit_no, prefecture, hall, model"
    )
    # prefecture フィルタ
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    # hall フィルタ
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    # model フィルタ
    if model not in (None, ALL):
        query = query.eq("model", model)
    # 実行
    rows = _fetch_all_rows(query)
    # 空なら空リストを返す
    if not rows:
        return []
    # DataFrame 化
    df = pd.DataFrame(rows)
    # unit_no の存在確認（万が一 VIEW に含まれない場合）
    if "unit_no" not in df.columns:
        return []
    # ユニーク台番号
    units = sorted(df["unit_no"].dropna().unique().tolist())

    return units


if __name__ == "__main__":

    view = "result_joined"
    start = "2025-11-01"
    end = "2025-11-30"
    hall = "楽園ハッピーロード大山"
    model = "マイジャグラーV"
    day_last = 3

    df = fetch(view, start, end, hall=hall, model=model, day_last=day_last)
    # res = query.execute()
    # df = pd.DataFrame(res.data)

    print(df.hall.unique())
    print(df.model.unique())
    print(df.date.unique())
    print(df)
    # print(df.tail())

    # df_one_day = fetch_one_day(view, "2025-11-13", hall=None, model=None)
    # print(df_one_day.date.unique())
    # print(df_one_day.shape[0])
