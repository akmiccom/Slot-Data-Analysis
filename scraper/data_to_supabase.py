import os
import pandas as pd
from supabase import create_client, Client

from config import config
from utils.logger_setup import setup_logger
# from app.data_from_supabase import get_supabase_client

# =========================
# 設定・ロガー
# =========================
filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def get_supabase_client() -> Client:
    """supabese のクライアントを取得"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が設定されていません。"
        )
    return create_client(url, key)


def add_model(df: pd.DataFrame, supabase: Client) -> None:
    """--- モデルの登録 (models) ---"""
    models = df["model"].dropna().unique().tolist()
    if not models:
        logger.warning("モデルなし")
        return

    # UNIQUE(models.name) 前提で upsert
    rows = [{"name": m} for m in models]
    supabase.table("models").upsert(rows, on_conflict="name").execute()
    logger.info(f"モデル upsert: {len(rows)} 件（新規/既存含む）")


def add_prefecture_and_hall(df: pd.DataFrame, supabase: Client) -> None:
    """--- 都道府県(prefectures) と ホール(halls) 登録 ---"""
    prefectures = df["pref"].dropna().unique().tolist()
    if not prefectures:
        logger.warning("pref カラムが空です。")
        return

    # 1) prefectures upsert
    pref_rows = [{"name": p} for p in prefectures]
    supabase.table("prefectures").upsert(pref_rows, on_conflict="name").execute()
    logger.info(f"都道府県 upsert: {len(pref_rows)} 件（新規/既存含む）")

    # 2) prefecture_id を取得してマップ化
    pref_res = supabase.table("prefectures").select("prefecture_id, name").execute()
    pref_map = {row["name"]: row["prefecture_id"] for row in pref_res.data}

    # 3) halls upsert（name + prefecture_id をユニークキー想定）
    hall_rows = []
    for pref in prefectures:
        pid = pref_map.get(pref)
        if not pid:
            logger.warning(f"⚠ prefecture_id 取得失敗: {pref}")
            continue
        halls = df.loc[df["pref"] == pref, "hall"].dropna().unique().tolist()
        for hall in halls:
            hall_rows.append({"name": hall, "prefecture_id": pid})

    if hall_rows:
        supabase.table("halls").upsert(
            hall_rows,
            on_conflict="name,prefecture_id",
        ).execute()
        logger.info(f"ホール upsert: {len(hall_rows)} 件（新規/既存含む）")
    else:
        logger.warning("ホールなし")


def add_data_result(df: pd.DataFrame, supabase: Client) -> None:
    """--- results テーブルへデータ登録 ---"""

    # 1) 最新の prefectures / halls / models を取得して ID マップを作る
    pref_res = supabase.table("prefectures").select("prefecture_id, name").execute()
    hall_res = supabase.table("halls").select("hall_id, name, prefecture_id").execute()
    model_res = supabase.table("models").select("model_id, name").execute()

    pref_map = {p["name"]: p["prefecture_id"] for p in pref_res.data}
    # (pref, hall) -> hall_id
    hall_map = {(h["prefecture_id"], h["name"]): h["hall_id"] for h in hall_res.data}
    model_map = {m["name"]: m["model_id"] for m in model_res.data}

    # 2) DataFrame から results 用レコードを作成
    records = []
    for _, row in df.iterrows():
        pref = row["pref"]
        hall_name = row["hall"]
        model_name = row["model"]

        pid = pref_map.get(pref)
        if not pid:
            logger.warning(f"⚠ prefecture_id なし: {pref}")
            continue

        hall_id = hall_map.get((pid, hall_name))
        if not hall_id:
            logger.warning(f"⚠ hall_id なし: {pref} / {hall_name}")
            continue

        model_id = model_map.get(model_name)
        if not model_id:
            logger.warning(f"⚠ model_id なし: {model_name}")
            continue

        try:
            unit_no = int(row["unit_no"])
            game = int(row["game"])
            bb = int(row["bb"])
            rb = int(row["rb"])
            medal = int(row["medal"])
        except (TypeError, ValueError):
            logger.warning(f"⚠ 数値変換エラー: {row}")
            continue

        records.append(
            {
                "hall_id": hall_id,
                "model_id": model_id,
                "unit_no": unit_no,
                "date": str(row["date"]),  # 'YYYY-MM-DD' 文字列でOK
                "game": game,
                "bb": bb,
                "rb": rb,
                "medal": medal,
            }
        )

    if not records:
        logger.warning("results に挿入するデータがありません。")
        return

    # 3) 一括 upsert（unique(hall_id, model_id, unit_no, date) を想定）
    #    行数が多い場合はバッチに分ける
    batch_size = 1000
    inserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        supabase.table("results").upsert(
            batch,
            on_conflict="hall_id,model_id,unit_no,date",
        ).execute()
        inserted += len(batch)

    logger.info(f"results upsert: {inserted} 件（新規/既存含む）")


if __name__ == "__main__":

    df = pd.read_csv(config.CSV_DIR / "cleaned_all_result_data.csv")
    
    # df = pd.read_csv("minrepo_01_from_sqlite.csv")
    # df["date"] = pd.to_datetime(df["date"]).dt.date

    # target_models = [
    #     "ハッピージャグラーVIII",
    #     "ジャグラーガールズ",
    #     "ファンキージャグラー2",
    #     "ネオアイムジャグラーEX",
    #     "マイジャグラーV",
    #     "ゴーゴージャグラー3",
    #     "ウルトラミラクルジャグラー",
    #     "ミスタージャグラー",
    #     "アイムジャグラーEX-TP",
    # ]

    # target_halls = [
    #     "コンサートホールエフ成増",
    #     "マルハン大山店",
    #     "マルハン青梅新町店",
    #     "大山オーシャン",
    #     "楽園ハッピーロード大山",
    #     "楽園池袋店",
    #     "楽園池袋店グリーンサイド",
    #     "スーパースロットサンフラワー+",
    #     "YASUDA9",
    #     "エクサファースト",
    #     "マルハン池袋店",
    # ]

    # df = df[df["hall"].isin(target_halls)]
    # df = df[df["model"].isin(target_models)]
    # df = df[(df["date"] >= "2025-11-01") & (df["date"] <= "2025-11-30")]

    print(df.date.unique())
    print(df.hall.unique())
    print(df.model.unique())
    print(df.shape[0])

    supabase = get_supabase_client()
    add_model(df, supabase)
    add_prefecture_and_hall(df, supabase)
    add_data_result(df, supabase)
