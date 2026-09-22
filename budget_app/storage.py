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

    def list(self, limit: int = 5) -> list[dict[str, Any]]:
        return heapq.nlargest(
            limit,
            self.read_transaction(),
            key=lambda transaction: transaction["date"]
        )

    def update(self, transaction_id: str, field_name : str, new_value) -> None:
        temp_path = self.file_path.with_suffix(".tmp")
        found = False

        try:
            with (
                self.file_path.open("r", encoding="utf-8") as source,
                temp_path.open("w", encoding="utf-8") as target,
            ):
                for line in source:
                    if not line.strip():
                        continue

                    transaction = json.loads(line)

                    if transaction["id"] == transaction_id:
                        transaction[field_name] = new_value
                        found = True

                    target.write(
                        json.dumps(transaction, ensure_ascii=False) + "\n"
                    )

            if not found:
                raise ValueError("해당 ID의 거래가 없습니다.")

            # 임시 -> 원본 교체
            temp_path.replace(self.file_path)

        finally:
            # 실패했을 때 남은 임시 파일 정리
            if temp_path.exists():
                temp_path.unlink()



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