import os
import re
import unicodedata
from supabase import create_client, Client

# =========================
# ユーティリティ
# =========================
def _norm_text(s: str | None) -> str:
    if s is None:
        return ""
    return str(s).strip()


def extract_model_name(text: str) -> str:
    """
    'ハッピージャグラーＶＩＩＩ　グラフ一覧' のような文字列から
    機種名だけ取り出して全角→半角に変換する関数
    """
    if not text:
        return ""

    # 1️⃣ 「グラフ一覧」などの末尾を除去（スペースや全角空白も考慮）
    name = re.sub(r"[　\s]*(グラフ一覧|一覧|データ一覧).*", "", text)

    # 2️⃣ 全角英数字・記号を半角に（例：ＶＩＩＩ → VIII）
    name = unicodedata.normalize("NFKC", name)

    # 3️⃣ 前後の空白をトリム
    name = name.strip()

    return name


def get_supabase_client() -> Client:
    """supabese のクライアントを取得"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が設定されていません。"
        )
    return create_client(url, key)
