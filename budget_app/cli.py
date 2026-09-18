import argparse
from .storage import TransactionRepository, CategoryRepository
from .services import *

def build_parser():
    parser = argparse.ArgumentParser(description="argument 설명")

    subparser = parser.add_subparsers(dest="command", required=True)
    subparser.add_parser("add", help="거래 추가 명령어")

    list_parser = subparser.add_parser("list", help="거래 목록 명령어")
    list_parser.add_argument("--limit", type=int, default=10, help="기본값 10")

    update_parser = subparser.add_parser("update", help="업데이트 명령어")
    update_parser.add_argument("--id", type=int, required=True, help="id int for update")
    update_parser.add_argument("--date", type=str, help="YYYY-MM-DD")

    delete_parser = subparser.add_parser("delete", help="삭제 명령어")
    delete_parser.add_argument("--id", type=int, required=True, help="id int for delete")

    search_parser = subparser.add_parser("search", help="검색 명령어")
    search_parser.add_argument("--from", dest="date_from", type=str, help="시작일 YYYY-MM-DD")
    search_parser.add_argument("--to", dest="date_to",type=str, help="종료일 YYYY-MM-DD")
    search_parser.add_argument("--category", type=str, help="카테고리")
    search_parser.add_argument("--type", type=str, help="income & expense")
    search_parser.add_argument("--q", type=str, help="메모")
    search_parser.add_argument("--tag", type=str, help="태그 쉼표로 구분")

    summary_parser = subparser.add_parser("summary", help="월별 요약 명령어")
    summary_parser.add_argument("--month", dest="date_month", type=str, help="YYYY-MM")

    budget_parser = subparser.add_parser("budget", help="예산 명령어")

    budget_subparser = budget_parser.add_subparsers(dest="budget_command", required=True)
    budget_set_parser = budget_subparser.add_parser("set", help="예산 설정")

    budget_set_parser.add_argument(
        "--month",
        dest="date_month",
        type=str,
        required=True,
        help="YYYY-MM",
    )
    budget_set_parser.add_argument(
        "--amount",
        type=int,
        required=True,
        help="예산 금액",
    )

    return parser


def add_transactions(service: TransactionService):
    while True:
        date_text = input("날짜를 입력하세요 (YYYY-MM-DD): ")

        try:
            service.validate_date(date_text=date_text)
            break
        except ValueError as error:
            print(f"[에러] {error}")

    while True:
        raw_type = input("타입을 입력하세요 (income / expense): ")

        try:
            transaction_type = service.validate_type(transaction_type=raw_type)
            break
        except ValueError as error:
            print(f"[에러] {error}")

    while True:
        category = input("등록할 카테고리를 입력하세요: ")

        try:
            service.validate_category(category=category)
            break
        except ValueError as error:
            print(f"[에러] {error}")

    while True:
        try:
            amount = int(input("금액(양수)을 입력하세요: "))

            if amount <= 0:
                raise ValueError("금액은 0보다 커야 합니다")

            break
        except ValueError as error:
            print(f"[에러] {error}")

    memo = input("(선택)메모를 입력하세요: ")
    raw_tag = input("태그를 쉼표로 구분하여 입력해주세요. 없으면 엔터를 클릭해주세요: ")
    transaction_tag = [tag.strip() for tag in raw_tag.split(",") if tag.strip()]

    transaction = service.add_transaction(
        date_text=date_text,
        transaction_type=transaction_type,
        category=category,
        amount=amount,
        memo=memo,
        tags=transaction_tag
    )

    print(f"[저장 완료] id = {transaction.id}")

def main():
    parser = build_parser()
    args = parser.parse_args()
    repository = TransactionRepository()
    category_repository = CategoryRepository()
    service = TransactionService(repository, category_repository)

    if args.command == "add":
        add_transactions(service)
    elif args.command == "list":
        list_transactions(limit=args.limit)
    elif args.command == "update":
        update_transactions(id=args.id)
    elif args.command == "delete":
        delete_transactions(id=args.id)
    elif args.command == "search":
        search_transactions(date_from=args.date_from, date_to=args.date_to, category=args.category, search_type=args.type)
    elif args.command == "summary":
        summary(date_month=args.date_month)
    elif args.command == "budget":
        if args.budget_command == "set":
            budget_set(date_month=args.date_month, amount=args.amount)


