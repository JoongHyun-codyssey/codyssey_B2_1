import heapq
from uuid import uuid4
from datetime import date
from pathlib import Path
from typing import Literal, Optional, Any, Iterator
from .storage import TransactionRepository, CategoryRepository
from .models import Transaction

space = "\n"

class TransactionService:
    def __init__(self, repository: TransactionRepository, category_repository: CategoryRepository):
        self.repository = repository
        self.category_repository = category_repository

    def add_transaction_service(
            self,
            date_text: str,
            transaction_type: Literal["income","expense"],
            category: str,
            amount: int,
            memo: str,
            tags: list[str]
            ) -> Transaction :
        transaction = Transaction(
            id=str(uuid4()),
            date=date_text,
            type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )

        self.repository.save(transaction)
        return transaction

    def list_transaction_service(self, limit:int)-> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("조회 개수는 1개 이상이어야 합니다.")
        return self.repository.list_n(limit=limit)

    def update_transaction_service(self, id:str, field_name:str, new_value) -> None:
        if field_name == "date":
            self.validate_date(new_value)
        elif field_name == "type":
            self.validate_type(new_value)
        elif field_name == "category":
            self.validate_category(new_value)
        elif field_name == "amount":
                if type(new_value) is not int or new_value <= 0:
                    raise ValueError("금액은 0보다 큰 정수여야 합니다.")

        self.repository.update(transaction_id=id, field_name=field_name, new_value=new_value)

    def delete_transactions_service(self, id: str) -> None:
        self.repository.delete(transaction_id=id)

    def search_transactions_service(
            self,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None,
            category: Optional[str] = None,
            search_type: Optional[Literal["income", "expense"]] = None,
            memo: Optional[str] = None,
            tag: Optional[str] = None,
    )-> Iterator[dict[str, Any]]:
        tmp = []
        chunk_paths = []
        temp_dir = Path("./data/tmp")

        if date_from is not None:
            self.validate_date(date_from)

        if date_to is not None:
            self.validate_date(date_to)

        if date_from is not None and date_to is not None:
            if date_from > date_to:
                raise ValueError("시작일은 종료일보다 늦을 수 없습니다.")

        if search_type is not None:
            self.validate_type(search_type)

        for transaction in self.repository.read_transaction():
            if category is not None and transaction["category"] != category:
                continue

            if search_type is not None and transaction["type"] != search_type:
                continue

            if date_from is not None and transaction["date"] < date_from:
                continue

            if date_to is not None and transaction["date"] > date_to:
                continue

            if memo is not None and memo not in transaction["memo"]:
                continue

            if tag is not None and tag not in transaction["tags"]:
                continue

            tmp.append(transaction)

            if len(tmp) >= 1000:
                tmp.sort(key=lambda tx:tx["date"], reverse=True)
                temp_path = temp_dir / f"chunk_{len(chunk_paths)}.jsonl"

                self.repository.write_chunk(tmp, temp_path)

                chunk_paths.append(temp_path)
                tmp.clear()

        if tmp:
            tmp.sort(key=lambda tx: tx["date"], reverse=True)

            temp_path = temp_dir / f"chunk_{len(chunk_paths)}.jsonl"
            self.repository.write_chunk(tmp, temp_path)

            chunk_paths.append(temp_path)
            tmp.clear()

        try:
            streams = [
                self.repository.read_jsonl(path)
                for path in chunk_paths
            ]

            yield from heapq.merge(
                *streams,
                key=lambda _transaction: _transaction["date"],
                reverse=True
            )
        finally:
            for path in chunk_paths:
                path.unlink()

            temp_dir.rmdir()

    @staticmethod
    def validate_type(transaction_type: str) -> Literal["income", "expense"]:
        if transaction_type == "income":
            return "income"

        if transaction_type == "expense":
            return "expense"

        raise ValueError("type은 income / expense만 입력이 가능합니다.")

    def validate_category(self, category: str) -> None:
        if not self.category_repository.exists(category):
            print(f"{space * 10}등록되지 않은 카테고리입니다.\n카테고리를 먼저 등록해주세요: {category}")
            quit()

    @staticmethod
    def validate_date(date_text: str)-> str:
        try:
            parsed_date = date.fromisoformat(date_text)
        except ValueError:
            raise ValueError(
                "실제 존재하는 날짜를 YYYY-MM-DD 형식으로 입력해 주세요."
            ) from None

        if parsed_date.isoformat() != date_text:
            raise ValueError("날짜는 YYYY-MM-DD 형식으로 입력해 주세요.")

        return date_text

def summary(date_month:str):
    print(f"summary + {date_month}")

def budget_set(date_month:str, amount:int):
    print(f"budget_set + {date_month} + {amount}")