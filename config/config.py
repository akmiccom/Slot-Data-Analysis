from pathlib import Path
from dataclasses import dataclass


MAIN_URL = "https://min-repo.com/tag/"

HALLS_YAML = "config/halls.yaml"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / DATA_DIR / "logs"
CSV_DIR = BASE_DIR / DATA_DIR / "csv"
IMG_DIR = BASE_DIR / DATA_DIR / "imgs"

LOG_PATH = LOG_DIR / 'minrepo.log'

for d in [DATA_DIR, LOG_DIR, CSV_DIR, IMG_DIR]:
    d.mkdir(exist_ok=True)


@dataclass
class HallInfo:
    name: str
    prefecture: str
    slug: str
    enabled: bool = True
    period: int = 2


if __name__ == "__main__":
    print(BASE_DIR)
