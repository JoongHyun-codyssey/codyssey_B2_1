from uuid import uuid4
from datetime import date

from typing import Literal
from typing import Optional
from .storage import TransactionRepository, CategoryRepository
from .models import Transaction

class TransactionService:
    def __init__(self, repository: TransactionRepository, category_repository: CategoryRepository):
        self.repository = repository
        self.category_repository = category_repository

    def add_transaction(
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

    @staticmethod
    def validate_type(transaction_type: str) -> Literal["income", "expense"]:
        if transaction_type == "income":
            return "income"

        if transaction_type == "expense":
            return "expense"

        raise ValueError("type은 income / expense만 입력이 가능합니다.")

    def validate_category(self, category: str) -> None:
        if not self.category_repository.exists(category):
            raise ValueError(f"등록되지 않은 카테고리입니다: {category}")

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

def list_transactions(limit: int = 10):
    print(f"list123 + {limit}")

def update_transactions(id: int):
    print(f"update + {id}")

def delete_transactions(id: int):
    print(f"delete + {id}")

def search_transactions(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        search_type: Optional[Literal["income", "expense"]] = None,
        memo: Optional[str] = None,
        tag: Optional[str] = None,
):
    print(f"search + {date_from} + {date_to} + {category} + {search_type} + {memo} + {tag}")

def summary(date_month:str):
    print(f"summary + {date_month}")

def budget_set(date_month:str, amount:int):
    print(f"budget_set + {date_month} + {amount}")