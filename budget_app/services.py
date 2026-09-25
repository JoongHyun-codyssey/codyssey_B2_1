import heapq
from uuid import uuid4
from datetime import date
from pathlib import Path
from typing import Literal, Optional, Any, Iterator, Generator
from .storage import TransactionRepository, CategoryRepository, BudgetRepository, read_jsonl
from .models import Transaction

space = "\n"

class TransactionService:
    def __init__(self,
                 repository: TransactionRepository,
                 category_repository: CategoryRepository,
                 budget_repository: BudgetRepository
                 ):
        self.repository = repository
        self.category_repository = category_repository
        self.budget_repository = budget_repository

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

    def delete_transaction_service(self, id: str) -> None:
        self.repository.delete(transaction_id=id)

    def search_transaction_service(
            self,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None,
            category: Optional[str] = None,
            search_type: Optional[Literal["income", "expense"]] = None,
            memo: Optional[str] = None,
            tag: Optional[str] = None,
    )-> Generator[dict[str, Any], None, None]:
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

        streams = []

        try:
            streams = [read_jsonl(path) for path in chunk_paths]

            yield from heapq.merge(
                *streams,
                key=lambda _transaction: _transaction["date"],
                reverse=True
            )
        finally:
            for stream in streams:
                stream.close()

            for path in chunk_paths:
                path.unlink(missing_ok=True)

            if temp_dir.exists():
                temp_dir.rmdir()

    def summary_transaction_service(
            self,
            date_month : str,
            top_n: Optional[int] = None,
            ):
        total_income = 0
        total_expense = 0
        category_expenses = {}
        top_categories = None
        warning_msg = None
        usage_rate = 0
        count = 0

        for transaction in self.repository.read_transaction():
            if transaction["date"][:7] != date_month:
                continue

            count += 1
            amount = transaction["amount"]

            if transaction["type"] == "income":
                total_income += amount
            else:
                total_expense += amount

                category = transaction["category"]

                category_expenses[category] = (
                    category_expenses.get(category, 0) + amount
                )

        # 잔액
        balance = total_income - total_expense

        # 지출 top 3
        if top_n is not None:
            if top_n <= 1:
                raise ValueError("TOP 개수는 1 이상이어야 합니다.")

            top_categories = heapq.nlargest(
                top_n,
                category_expenses.items(),
                key=lambda item:item[1],
            )

        budget_amount = self.budget_repository.get_amount(month=date_month)

        if budget_amount is not None:
            if budget_amount <= 0:
                raise ValueError("예산은 0보다 커야 합니다.")

            # 예산 사용률
            usage_rate = total_expense / budget_amount * 100

            if total_expense > usage_rate:
                warning_msg = "예산 대비 사용률이 초과했습니다!"

        else:
            budget_amount = 0

        return {
            "count" : count,
            "total_income" : total_income,
            "total_expense" : total_expense,
            "balance" : balance,
            "top_categories" : top_categories,
            "budget_amount" : budget_amount,
            "usage_rate" : usage_rate,
            "warning_msg" : warning_msg
        }

    def budget_set(self, date_month: str, amount: int) -> None:
        month_text = self.validate_month(date_month)

        if type(amount) is not int or amount <= 0:
            raise ValueError("예산은 0보다 큰 정수여야 합니다.")

        self.budget_repository.set_amount(month=date_month, amount=amount)

    def category_set(self, category_name : str) -> None:
        category_name = category_name.strip()

        if not category_name:
            raise ValueError("카테고리 이름을 입력해주세요.")

        self.category_repository.add_category(category_name)

    def category_list(self) -> Iterator[str]:
        return self.category_repository.read_categories()

    def category_remove(self, category_name:str) -> None:
        if not category_name:
            raise ValueError("카테고리 이름을 입력해주세요.")

        if not self.category_repository.exists(category_name):
            raise ValueError("등록되지 않은 카테고리입니다.")

        # self.repository는 생성자에서 받은 TransactionRepository 객체
        for transaction in self.repository.read_transaction():
            if transaction["category"] == category_name:
                raise ValueError("거래에서 사용 중인 카테고리는 삭제할 수 없습니다.")

        self.category_repository.remove_category(category_name)

    def export_transaction_service(self,
                                   out_path: str,
                                   date_month: Optional[str] = None,
                                   date_from: Optional[str] = None,
                                   date_to: Optional[str] = None,
                                   ) -> int :
        if not out_path.strip():
            raise ValueError("출력 파일 경로를 입력해 주세요.")

        output_path = self.repository.file_path.parent / out_path

        if output_path.suffix.lower() != ".csv":
            raise ValueError("출력 파일은 .csv 확장자여야 합니다.")

        if output_path.is_dir():
            raise ValueError("파일 경로를 입력해 주세요.")

        if not output_path.parent.is_dir():
            raise ValueError("저장할 폴더가 존재하지 않습니다.")

        if date_month is None and (date_from is None or date_to is None):
            raise ValueError(
                "--month 또는 --from과 --to를 함께 입력해야 합니다."
            )

        def filtered_transaction() -> Iterator[dict[str, Any]]:
            transactions = self.search_transaction_service(
                date_from=date_from,
                date_to=date_to,
            )

            try:
                for transaction in transactions:
                    if date_month is not None:
                        if transaction["date"][:7] != date_month:
                            continue

                    yield transaction
            finally:
                transactions.close()

        return self.repository.export_csv(
            output_path=output_path,
            transactions=filtered_transaction()
        )

    def import_transaction_service(self, input_path: str) -> tuple[int, int]:
        skipped_count = 0

        if not input_path.strip():
            raise ValueError("가져올 파일 경로를 입력해 주세요.")

        csv_path = self.repository.file_path.parent / input_path

        if csv_path.suffix.lower() != ".csv":
            raise ValueError("CSV 파일만 가져올 수 있습니다.")

        if not csv_path.is_file():
            raise ValueError("가져올 파일이 존재하지 않거나 파일이 아닙니다.")

        def validated_transactions() -> Iterator[dict[str, Any]]:
            nonlocal skipped_count

            # 기존 거래와 CSV 내부의 ID 중복 확인용
            seen_ids = {
                transaction["id"]
                for transaction in self.repository.read_transaction()
            }

            for row in self.repository.read_csv(csv_path):
                transaction_id = row["id"].strip()

                if not transaction_id:
                    raise ValueError("거래 ID가 비어 있습니다.")

                if transaction_id in seen_ids:
                    skipped_count += 1
                    continue

                date_text = self.validate_date(row["date"])
                transaction_type = self.validate_type(row["type"])
                self.validate_category(row["category"])

                try:
                    amount = int(row["amount"])
                except ValueError:
                    raise ValueError("금액은 정수여야 합니다.") from None

                if amount <= 0:
                    raise ValueError("금액은 0보다 커야 합니다.")

                transaction: dict[str, Any] = {
                    "id": transaction_id,
                    "date": date_text,
                    "type": transaction_type,
                    "category": row["category"],
                    "amount": amount,
                    "memo": row["memo"],
                    "tags": [
                        tag.strip()
                        for tag in row["tags"].split(",")
                        if tag.strip()
                    ],
                }

                seen_ids.add(transaction_id)
                yield transaction

        imported_count = self.repository.import_transactions(
            transactions=validated_transactions()
        )

        return imported_count, skipped_count


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

    @staticmethod
    def validate_month(month_text: str) -> str:
        try:
            parsed_date = date.fromisoformat(month_text + "-01")
        except ValueError:
            raise ValueError(
                "올바른 월을 YYYY-MM 형식으로 입력해 주세요."
            ) from None

        if parsed_date.isoformat()[:7] != month_text:
            raise ValueError("월은 YYYY-MM 형식으로 입력해 주세요.")

        return month_text