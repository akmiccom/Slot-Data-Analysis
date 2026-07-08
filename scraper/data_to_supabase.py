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


def add_data_result(df: pd.DataFrame, supabase: Client) -> int:
    """--- results テーブルへデータ登録 ---

    Returns:
        upsert 対象として送信できた件数（新規/既存更新を含む）
    """

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
        return 0

    conflict_keys = ["hall_id", "model_id", "unit_no", "date"]
    before_dedup = len(records)
    records_df = pd.DataFrame(records)
    duplicate_count = records_df.duplicated(subset=conflict_keys, keep=False).sum()
    logger.info("results upsert前の重複件数(%s): %d 件", conflict_keys, duplicate_count)
    if duplicate_count:
        records_df = records_df.drop_duplicates(subset=conflict_keys, keep="last")
        logger.info("results upsert前の重複除去: %d 件 -> %d 件", before_dedup, len(records_df))
    records = records_df.to_dict("records")
    logger.info("results upsert対象件数: %d 件", len(records))

    # 3) 一括 upsert（unique(hall_id, model_id, unit_no, date) を想定）
    #    行数が多い場合はバッチに分ける
    batch_size = 1000
    inserted = 0
    for i in range(0, len(records), batch_size):
        batch_no = i // batch_size + 1
        batch = records[i : i + batch_size]
        logger.info("results upsert batch %d: %d 件", batch_no, len(batch))
        try:
            supabase.table("results").upsert(
                batch,
                on_conflict="hall_id,model_id,unit_no,date",
            ).execute()
        except Exception:
            key_samples = [
                {key: record.get(key) for key in ["hall_id", "model_id", "unit_no", "date"]}
                for record in batch[:5]
            ]
            logger.exception(
                "results upsert失敗: batch=%d, 件数=%d, key_samples=%s",
                batch_no,
                len(batch),
                key_samples,
            )
            raise
        inserted += len(batch)

    logger.info(f"results upsert: {inserted} 件（新規/既存含む）")
    return inserted


if __name__ == "__main__":

    df = pd.read_csv(config.CSV_DIR / "cleaned_all_result_data.csv")
    
    logger.debug("date unique: %s", df.date.unique())
    logger.debug("hall unique: %s", df.hall.unique())
    logger.debug("model unique: %s", df.model.unique())
    logger.debug("row count: %d", df.shape[0])

    supabase = get_supabase_client()
    add_model(df, supabase)
    add_prefecture_and_hall(df, supabase)
    add_data_result(df, supabase)
