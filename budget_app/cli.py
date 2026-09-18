import argparse
from budget_app.services import *

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

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        add()
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


