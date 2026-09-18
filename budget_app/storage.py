import json
from dataclasses import asdict
from pathlib import Path

from .models import Transaction


class TransactionRepository:
    def __init__(self, data_dir: str = "./data"):
        self.file_path = Path(data_dir) / "transactions.jsonl"

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.touch(exist_ok=True)

    def save(self, transaction: Transaction) -> None:
        transaction_data = asdict(transaction)

        json_line = json.dumps(transaction_data, ensure_ascii=False)

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(json_line + "\n")

class CategoryRepository:
    def __init__(self, data_dir: str = "./data"):
        self.file_path = Path(data_dir) / "categories.jsonl"

    def exists(self, category: str) -> bool:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                data = json.loads(line)

                if data["name"] == category:
                    return True

        return False