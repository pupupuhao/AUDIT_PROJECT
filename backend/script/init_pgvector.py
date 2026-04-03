import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.pgvector import PgVectorStore


def run():
    store = PgVectorStore()
    store.init_schema()
    print("pgvector 表结构初始化完成。")


if __name__ == "__main__":
    run()
