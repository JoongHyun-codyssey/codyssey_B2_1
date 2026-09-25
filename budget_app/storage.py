import csv
import json
import heapq
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Any, Optional, Generator

from .models import Transaction

def read_jsonl(file_path: Path) -> Generator[dict[str, Any], None, None]:
    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            yield json.loads(line)

def atomic_write_jsonl(
    file_path: Path,
    records: Iterator[dict[str, Any]],
) -> None:
    temp_path = file_path.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as target:
            for record in records:
                target.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

        # 쓰기가 끝나고 파일이 닫힌 뒤 교체
        temp_path.replace(file_path)

    finally:
        if temp_path.exists():
            temp_path.unlink()


class TransactionRepository:
    def __init__(self, data_dir: str = "./data"):
        self.file_path = Path(data_dir) / "transactions.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.touch(exist_ok=True)

    def read_transaction(self) -> Iterator[dict[str, Any]]:
        yield from read_jsonl(self.file_path)

    def save(self, transaction: Transaction) -> None:
        def added_records() -> Iterator[dict[str, Any]]:
            yield from read_jsonl(self.file_path)
            yield asdict(transaction)

        atomic_write_jsonl(self.file_path, added_records())

    # 최신 N개용 정렬 메서드
    def list_n(self, limit: int = 5) -> list[dict[str, Any]]:
        return heapq.nlargest(
            limit,
            self.read_transaction(),
            key=lambda transaction: transaction["date"]
        )

    def update(self, transaction_id: str, field_name : str, new_value) -> None:
        def update_records() -> Iterator[dict[str, Any]]:
            found = False

            for transaction in read_jsonl(self.file_path):
                if transaction["id"] ==  transaction_id:
                    transaction[field_name] = new_value
                    found = True

                yield  transaction

            if not found:
                raise ValueError("해당 ID의 거래가 없습니다.")

        atomic_write_jsonl(
            self.file_path,
            update_records()
        )

    def delete(self, transaction_id : str) -> None:
        def delete_records() -> Iterator[dict[str, Any]]:
            found = False

            for transaction in read_jsonl(self.file_path):
                if transaction["id"] == transaction_id:
                    found = True
                    continue

                yield transaction

            if not found:
                raise ValueError("해당 ID의 거래가 없습니다.")

        atomic_write_jsonl(
            self.file_path,
            delete_records()
        )

    def export_csv(self,
                   output_path: Path,
                   transactions: Iterator[dict[str, Any]]) -> int:
        count = 0
        temp_path = output_path.with_suffix(".tmp")

        print("export_csv 호출됨")
        print("저장 위치:", output_path.resolve())

        try:
            with temp_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["id", "type", "date", "amount", "category", "memo", "tags"],
                )
                writer.writeheader()

                for transaction in transactions:
                    row = transaction.copy()
                    row["tags"] = ", ".join(transaction["tags"])

                    writer.writerow(row)
                    count += 1

            temp_path.replace(output_path)

            return count

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def read_csv(self, input_path = Path) -> Iterator[dict[str, str]]:
        required_fields = {
            "id", "type", "date", "amount", "category", "memo", "tags"
        }

        with input_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise ValueError("CSV 헤더가 없습니다.")

            if not required_fields.issubset(reader.fieldnames):
                raise ValueError("CSV에 필수 컬럼이 누락되어 있습니다.")

            for row in reader:
                if None in row:
                    raise ValueError(
                        f"CSV {reader.line_num}줄: 컬럼보다 값이 많습니다."
                    )

                if any(value is None for value in row.values()):
                    raise ValueError(
                        f"CSV {reader.line_num}줄: 값이 누락된 컬럼이 있습니다."
                    )

                yield row

    def import_transactions(
            self,
            transactions: Iterator[dict[str, Any]],
    ) -> int:
        count = 0

        def combined_records() -> Iterator[dict[str, Any]]:
            nonlocal count

            # 기존 거래 유지
            yield from read_jsonl(self.file_path)

            # 서비스에서 검증하며 전달하는 새 거래 추가
            for transaction in transactions:
                yield transaction
                count += 1

        atomic_write_jsonl(
            self.file_path,
            combined_records(),
        )

        return count

    def write_chunk(
        self,
        transactions: list[dict[str, Any]],
        temp_path: Path,
        ) -> None:
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with temp_path.open("w", encoding="utf-8") as file:
            for transaction in transactions:
                file.write(
                    json.dumps(transaction, ensure_ascii=False) + "\n"
                )


class CategoryRepository:
    def __init__(self, data_dir: str = "./data"):
        self.file_path = Path(data_dir) / "categories.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.touch(exist_ok=True)

    def add_category(self, category_name : str) -> None:
        if self.exists(category_name):
            raise ValueError("이미 존재하는 카테고리입니다.")

        def add_records() -> Iterator[dict[str, Any]]:
            yield from read_jsonl(self.file_path)
            yield {"name": category_name}

        atomic_write_jsonl(self.file_path, add_records())

    def read_categories(self) -> Iterator[str]:
        for category in read_jsonl(self.file_path):
            yield category["name"]

    def remove_category(self, category_name: str) -> None:
        def remaining_records() -> Iterator[dict[str, Any]]:
            found = False

            for category in read_jsonl(self.file_path):
                if category["name"] == category_name:
                    found = True
                    continue

                yield category

            if not found:
                raise ValueError("등록되지 않은 카테고리입니다.")

        atomic_write_jsonl(self.file_path, remaining_records())

    def exists(self, category: str) -> bool:
        for data in read_jsonl(self.file_path):
            if data["name"] == category:
                return True

        return False

class BudgetRepository:
    def __init__(self, data_dir: str = "./data"):
        self.file_path = Path(data_dir) / "budgets.jsonl"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.touch(exist_ok=True)

    def set_amount(self, month: str, amount: int) -> None:
        def budget_records() -> Iterator[dict[str, Any]]:
            found = False

            for budget in read_jsonl(self.file_path):
                if budget["month"] == month:
                    budget["amount"] = amount
                    found = True

                yield budget

            if not found:
                yield {"month": month, "amount": amount}

        atomic_write_jsonl(self.file_path, budget_records())

    def get_amount(self, month: str) -> Optional[int]:
        for budget in read_jsonl(self.file_path):
            if budget["month"] == month:
                return budget["amount"]

        return None
