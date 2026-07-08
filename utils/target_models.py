import unicodedata
from pathlib import Path

import yaml

from config import config
from utils.logger_setup import setup_logger

logger = setup_logger(__name__, log_file=config.LOG_PATH)

PREFIXES_TO_STRIP = ("S", "L")
TARGET_MODELS_YAML = config.BASE_DIR / "config" / "target_models.yaml"


def normalize_model_name(text: str | None, strip_prefix: bool = True) -> str:
    """機種名比較用に表記ゆれを正規化する。"""
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("Ⅴ", "V").replace("ⅴ", "V")
    normalized = "".join(normalized.split())
    if strip_prefix:
        while len(normalized) > 1 and normalized[0].upper() in PREFIXES_TO_STRIP:
            normalized = normalized[1:]
    return normalized.upper()


def load_target_models(path: str | Path = TARGET_MODELS_YAML) -> list[dict]:
    """target_models.yaml を読み込む。"""
    path = Path(path)
    if not path.exists():
        logger.warning("target_models.yaml が見つかりません: %s", path)
        return []

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    target_models = data.get("target_models") or []
    if not target_models:
        logger.warning("target_models.yaml が空です: %s", path)
    return target_models


def build_alias_to_canonical(target_models: list[dict] | None = None) -> dict[str, str]:
    """正規化済み alias -> canonical_name の辞書を作成する。"""
    if target_models is None:
        target_models = load_target_models()

    alias_to_canonical: dict[str, str] = {}
    for item in target_models:
        if not item or not item.get("enabled", True):
            continue

        canonical_name = item.get("canonical_name")
        if not canonical_name:
            logger.warning("canonical_name がない target_models.yaml エントリがあります: %s", item)
            continue

        aliases = item.get("aliases") or []
        if not aliases:
            logger.warning("aliases がない target_models.yaml エントリがあります: %s", canonical_name)
            continue

        for alias in aliases:
            normalized_alias = normalize_model_name(alias)
            if normalized_alias:
                alias_to_canonical[normalized_alias] = canonical_name

    if not alias_to_canonical:
        logger.warning("target_models.yaml から有効な aliases を読み込めませんでした。")
    return alias_to_canonical


def match_target_model(raw_model_name: str, alias_to_canonical: dict[str, str]) -> str | None:
    """正規化 + aliases + 部分一致で対象機種に一致する canonical_name を返す。"""
    normalized_raw = normalize_model_name(raw_model_name)
    if not normalized_raw:
        return None

    for normalized_alias, canonical_name in alias_to_canonical.items():
        if normalized_alias == normalized_raw or normalized_alias in normalized_raw or normalized_raw in normalized_alias:
            return canonical_name
    return None
