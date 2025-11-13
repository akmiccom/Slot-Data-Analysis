import pandas as pd
from utils.utils import get_supabase_client


def fetch(view: str, start: str, end: str, hall: str = None, model: str = None):
    """
    supabase からデータ呼び出し
    hall, model を指定しない場合はすべてを呼び出し
    """
    supabase = get_supabase_client()
    query = (
        supabase.table(view).select("*").gte("date", start).lte("date", end)
    )
    if hall is not None:
        query = query.eq("hall", hall)
    if model is not None:
        query = query.eq("model", model)

    res = query.execute()
    df = pd.DataFrame(res.data)

    return df


if __name__ == "__main__":

    view = "result_joined"
    start = "2025-11-10"
    end = "2025-11-10"
    # hall = "楽園ハッピーロード大山"
    # model = "マイジャグラーV"

    df = fetch(view, start, end, hall=None, model=None)
    # res = query.execute()
    # df = pd.DataFrame(res.data)

    print(df.hall.unique())
    print(df.model.unique())
    print(df.shape)
    print(df.tail())
