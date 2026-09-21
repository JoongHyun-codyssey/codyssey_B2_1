import json
import heapq
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Any

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

    def read_transaction(self)-> Iterator[dict[str, Any]]:
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                yield json.loads(line)

    def list(self, limit: int = 10) -> list[dict[str, Any]]:
        return heapq.nlargest(
            limit,
            self.read_transaction(),
            key=lambda transaction: transaction["date"]
        )

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