import os
from typing import Optional
import pandas as pd
from supabase import create_client, Client


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
def _fetch_all_rows(query, page_size: int = 1000) -> list[dict[str, any]]:
    """
    Supabase の 1000件制限を回避するための共通関数。
    渡された query に対して range() でページングしながら全件取得する。
    """
    all_rows: list[dict[str, any]] = []
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


# def fetch(view: str, start: str, end: str, hall: str = None, model: str = None):
#     """
#     Supabase からデータをページングしてすべて取得する。
#     hall, model を指定しない場合はすべてを呼び出し
#     API の 1000 件制限を回避。
#     """
#     supabase = get_supabase_client()

#     page_size = 1000
#     page = 0
#     all_rows = []

#     while True:
#         # ベースクエリ
#         query = supabase.table(view).select("*").gte("date", start).lte("date", end)

#         if hall is not None:
#             query = query.eq("hall", hall)

#         if model is not None:
#             query = query.eq("model", model)

#         # ページング
#         start_i = page * page_size
#         end_i = start_i + page_size - 1
#         query = query.range(start_i, end_i)

#         res = query.execute()
#         rows = res.data
#         if not rows:  # データが0件になったら終了
#             break

#         all_rows.extend(rows)
#         page += 1

#     df = pd.DataFrame(all_rows)

#     return df


# --------------------------------------------------
# ① 期間指定＆hall/model でフィルタ（既存 fetch の改良版）
# --------------------------------------------------
def fetch(
    view: str,
    start: str,
    end: str,
    hall: Optional[str] = None,
    model: Optional[str] = None,
) -> pd.DataFrame:
    """
    Supabase から date 範囲でデータ取得。
    hall, model を指定しない場合はすべてを取得。
    内部でページングして 1000件制限を回避する。
    """
    supabase = get_supabase_client()
    query = supabase.table(view).select("*").gte("date", start).lte("date", end)
    if hall is not None:
        query = query.eq("hall", hall)
    if model is not None:
        query = query.eq("model", model)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)

    return df


# --------------------------------------------------
# ② 1日分だけ取得するヘルパー
# --------------------------------------------------
def fetch_one_day(
    view: str, target_date: str, hall: Optional[str] = None, model: Optional[str] = None
) -> pd.DataFrame:
    """
    指定した1日分（target_date）のデータを取得する。
    内部的には fetch() を start=end にして呼び出すだけ。
    """
    return fetch(view=view, start=target_date, end=target_date, hall=hall, model=model)


# --------------------------------------------------
# ③ 最新日（最大 date）のデータを取得するヘルパー
# --------------------------------------------------
def fetch_latest(
    view: str, hall: Optional[str] = None, model: Optional[str] = None
) -> pd.DataFrame:
    """
    指定 view について、date が最大の日付のデータを取得する。
    hall / model を指定した場合は、その条件内での最新日を対象とする。
    """
    supabase = get_supabase_client()

    # まず最新日だけを1行取得
    query = supabase.table(view).select("date").order("date", desc=True).limit(1)

    if hall is not None:
        query = query.eq("hall", hall)
    if model is not None:
        query = query.eq("model", model)

    res = query.execute()
    rows = res.data

    if not rows:
        # データなしの場合は空の DataFrame を返す
        return pd.DataFrame()

    latest_date = rows[0]["date"]
    # その最新日について1日分を取得
    return fetch_one_day(view=view, target_date=latest_date, hall=hall, model=model)


# --------------------------------------------------
# ④ マスタ系：halls / models（& おまけで prefectures）
# --------------------------------------------------
def fetch_halls() -> pd.DataFrame:
    """
    halls テーブルの全件を取得（必要ならページング対応も可能）。
    """
    supabase = get_supabase_client()
    query = supabase.table("halls").select("*").order("name")
    rows = _fetch_all_rows(query)
    return pd.DataFrame(rows)


def fetch_models() -> pd.DataFrame:
    """
    models テーブルの全件を取得。
    """
    supabase = get_supabase_client()
    query = supabase.table("models").select("*").order("name")
    rows = _fetch_all_rows(query)
    return pd.DataFrame(rows)


def fetch_prefectures() -> pd.DataFrame:
    """
    prefectures テーブルの全件を取得（おまけ）。
    """
    supabase = get_supabase_client()
    query = supabase.table("prefectures").select("*").order("name")
    rows = _fetch_all_rows(query)
    return pd.DataFrame(rows)


# --------------------------------------------------
# ⑤ 汎用版：任意の条件 dict を渡せる fetch_paginated
# --------------------------------------------------
def fetch_paginated(
    view: str,
    eq_filters: Optional[dict[str, any]] = None,
    gte_filters: Optional[dict[str, any]] = None,
    lte_filters: Optional[dict[str, any]] = None,
    order_by: Optional[str] = None,
    desc: bool = False,
) -> pd.DataFrame:
    """
    任意のテーブル(view)に対して、eq/gte/lte 条件を dict で渡して
    ページングしながら全件取得する汎用関数。
    例:
        df = fetch_paginated(
            "results_view",
            eq_filters={"hall": "新宿ホール", "model": "マイジャグラーV"},
            gte_filters={"date": "2024-01-01"},
            lte_filters={"date": "2024-12-31"},
            order_by="date",
            desc=False,
        )
    """
    supabase = get_supabase_client()
    query = supabase.table(view).select("*")
    # eq 条件
    if eq_filters:
        for col, val in eq_filters.items():
            query = query.eq(col, val)
    # gte 条件
    if gte_filters:
        for col, val in gte_filters.items():
            query = query.gte(col, val)
    # lte 条件
    if lte_filters:
        for col, val in lte_filters.items():
            query = query.lte(col, val)
    # order by
    if order_by:
        query = query.order(order_by, desc=desc)
    rows = _fetch_all_rows(query)

    return pd.DataFrame(rows)


if __name__ == "__main__":

    view = "result_joined"
    start = "2025-11-10"
    end = "2025-11-15"
    hall = "楽園ハッピーロード大山"
    model = "マイジャグラーV"

    df = fetch(view, start, end, hall=None, model=None)
    # res = query.execute()
    # df = pd.DataFrame(res.data)

    print(df.hall.unique())
    print(df.model.unique())
    print(df.date.unique())
    print(df.shape[0])
    # print(df.tail())

    df_one_day = fetch_one_day(view, "2025-11-13", hall=None, model=None)
    print(df_one_day.date.unique())
    print(df_one_day.shape[0])
