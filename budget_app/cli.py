from argparse import ArgumentParser
from typing import Literal
import argparse
from .storage import TransactionRepository, CategoryRepository
from .services import *

def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="argument 설명")

    subparser = parser.add_subparsers(dest="command", required=True)
    subparser.add_parser("add", help="거래 추가 명령어")

    list_parser = subparser.add_parser("list", help="거래 목록 명령어")
    list_parser.add_argument("--limit", type=int, default=10, help="기본값 10")

    update_parser = subparser.add_parser("update", help="업데이트 명령어")
    update_parser.add_argument("--id", type=str, required=True, help="[require] id str for update")

    delete_parser = subparser.add_parser("delete", help="삭제 명령어")
    delete_parser.add_argument("--id", type=str, required=True, help="id str for delete")

    search_parser = subparser.add_parser("search", help="검색 명령어")
    search_parser.add_argument("--from", dest="date_from", type=str, help="시작일 YYYY-MM-DD")
    search_parser.add_argument("--to", dest="date_to",type=str, help="종료일 YYYY-MM-DD")
    search_parser.add_argument("--category", type=str, help="카테고리")
    search_parser.add_argument("--type", type=str, help="income & expense")
    search_parser.add_argument("--q", type=str, help="메모")
    search_parser.add_argument("--tags", type=str, help="태그 쉼표로 구분")

    summary_parser = subparser.add_parser("summary", help="월별 요약 명령어")
    summary_parser.add_argument("--month", dest="date_month", type=str, help="YYYY-MM")
    summary_parser.add_argument("--top", dest="top_n", type=int, help="카테고리별 지출 상위 N개 (기본값: 3)",)

    budget_parser = subparser.add_parser("budget", help="예산 명령어")
    budget_subparser = budget_parser.add_subparsers(dest="budget_command", required=True)
    budget_set_parser = budget_subparser.add_parser("set", help="예산 설정")

    category_parser = subparser.add_parser("category", help="카테고리 추가/수정/삭제 명령어")
    category_subparser = category_parser.add_subparsers(dest="category_command", required=True)
    category_add_parser = category_subparser.add_parser("add", help="카테고리 추가")
    category_list_parser = category_subparser.add_parser("list", help="카테고리 리스트")
    category_remove_parser = category_subparser.add_parser("remove", help="카테고리 삭제")

    export_parser = subparser.add_parser("export", help="CSV 내보내기 명령어")
    export_parser.add_argument("--out", dest="export_out", required=True, type=str, help="[file name].csv")
    export_parser.add_argument("--month", dest="export_month", type=str, help="export month: YYYY-MM")
    export_parser.add_argument("--from", dest="export_month_from", type=str, help="export month_from: YYYY-MM-DD")
    export_parser.add_argument("--to", dest="export_month_to", type=str, help="export month_to: YYYY-MM-DD")



    import_parser = subparser.add_parser("import", help="CSV 가져오기 명령어")
    import_parser.add_argument("--from", dest="import_from", type=str, help="[file name].csv")

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

# 거래 추가
def add_transactions(service: TransactionService) -> None:
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
        except OSError as error:
            print(f"[파일 읽기 오류] {error}")
            return

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

    try:
        transaction = service.add_transaction_service(
            date_text=date_text,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=transaction_tag
        )
    except ValueError as error:
        print(f"[입력 또는 데이터 오류] {error}")
    except OSError as error:
        print(f"[파일 처리 오류] {error}")
    else:
        print(f"[저장 완료] id = {transaction.id}")

# 목록 조회
def list_transactions(service: TransactionService, limit)-> None:
    data = service.list_transaction_service(limit)
    for list_data in data:
        print(
            f"{list_data['id']} | {list_data['date']} | {list_data['type']} | {list_data['category']} | {list_data['amount']} | {list_data['memo']} | {', '.join(list_data['tags'])}")

## 수정 ( B안 - 대화형 기반 )
def update_transactions(
        service: TransactionService,
        args_id:str
    ) -> None:

    while True:
        raw_choice = input("수정할 필드를 선택하세요.\n1.날짜\n2.타입\n3.카테고리\n4.가격\n5.메모\n6.태그\n번호를 입력하세요: ")
        try:
            field_choice = int(raw_choice)
            if field_choice not in(1,2,3,4,5,6):
                raise ValueError(f"범위에 맞는 번호를 선택해주세요.\n{field_choice}")
            break
        except ValueError:
            print(f"잘못 입력되었습니다.\n{raw_choice}")


    field_map = {
        1: "date",
        2: "type",
        3: "category",
        4: "amount",
        5: "memo",
        6: "tags",
    }

    field_name = field_map[field_choice]

    while True:
        raw_value = input(f"{field_name}의 새 값을 입력하세요: ")

        try:
            if field_name == "amount":
                new_value = int(raw_value)
            elif field_name == "tags":
                new_value = [
                    tag.strip()
                    for tag in raw_value.split(",")
                    if tag.strip()
                ]
            else:
                new_value = raw_value

            service.update_transaction_service(
                id=args_id,
                field_name=field_name,
                new_value=new_value
            )
            break

        except ValueError as error:
            print(f"[에러]: {error}")


    print(f"[수정 완료] id = {args_id}")

# 삭제
def delete_transactions(
    service: TransactionService,
    args_id: str
    ) -> None:
    confirmation = input("정말 삭제하시겠습니까? (y/n): ").strip().lower()

    if confirmation != "y":
        print("삭제를 취소합니다.")
        return

    try:
        service.delete_transactions_service(id=args_id)
    except ValueError as error:
        print(f"[에러]: {error}")
    else:
        print(f"[삭제 완료] id = {args_id}")

# 검색 스트리밍 처리
def search_transactions(
        service: TransactionService,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        search_type: Optional[Literal["income", "expense"]] = None,
        memo: Optional[str] = None,
        tag: Optional[str] = None,
) -> None:
    try:
        transactions = service.search_transaction_service(
            date_from=date_from,
            date_to=date_to,
            category=category,
            search_type=search_type,
            memo=memo,
            tag=tag
        )

        found = False

        for transaction in transactions:
            found = True
            print(f"[검색 결과] {transaction['id']} | {transaction['date']} | {transaction['type']} | {transaction['category']} | {transaction['amount']} | {transaction['memo']} | {', '.join(transaction['tags'])}")

        if not found:
            print("검색 결과가 없습니다.")

    except ValueError as error:
        print(f"[에러]: {error}")

def summary_transactions(
        service: TransactionService,
        date_month: str,
        top_n: Optional[int] = None,
)-> None:
    try:
        result = service.summary_transaction_service(date_month=date_month, top_n=top_n)

        if result["count"] == 0:
            print("해당 월의 거래 내역이 없습니다.")
            return

        print(
            f"총 수입: {result['total_income']}원\n"
            f"총 지출: {result['total_expense']}원\n"
            f"잔액: {result['balance']}원\n"
            f"예산: {result['budget_amount']}원 (사용률 {result['usage_rate']}%)\n"
        )

        if result["warning_msg"] is not None:
            print(f"{result['warning_msg']}\n")

        top_categories = result["top_categories"]
        if top_categories is not None:
            if not top_categories:
                print("지출 내역이 없습니다.")
            else:
                print(f"지출 TOP {top_n}")

                for rank, (category, amount) in enumerate(top_categories, start=1):
                    print(f"{rank}) {category} {amount:,}원")

            # print(
            #     f"지출 TOP 3\n"
            #     f"1) {result['top_categories'][0][0]} {result['top_categories'][0][1]}원\n"
            #     f"2) {result['top_categories'][1][0]} {result['top_categories'][1][1]}원\n"
            #     f"3) {result['top_categories'][2][0]} {result['top_categories'][2][1]}원\n"
            # )

    except ValueError as error:
        print(f"잘못된 입력입니다. {error}")


def budget_transactions(
        service: TransactionService,
        date_month: str,
        amount: int
) -> None:
    try:
        service.budget_set(date_month=date_month, amount=amount)
    except ValueError as error:
        print(f"[입력 또는 데이터 오류]: {error}")
    except OSError as error:
        print(f"[파일 저장 오류]: {error}")
    else:
        print(f"[저장 완료] {date_month} 예산: {amount:,}원")

def category_add(service:TransactionService) -> None:
    while True:
        category_name = input("카테고리명: ")

        try:
            service.category_set(category_name=category_name)
        except ValueError as error:
            print(f"[에러] {error}")
        except OSError as error:
            print(f"[파일 처리 오류] {error}")
            return
        else:
            print(f"[추가 완료] category={category_name.strip()}")
            break

def category_list(service: TransactionService):
    try:
        categories = service.category_list()
        found = False

        for name in categories:
            found = True
            print(f"- {name}")

        if not found:
            print("등록된 카테고리가 없습니다.")

    except ValueError as error:
        print(f"[데이터 오류] {error}")
    except OSError as error:
        print(f"[파일 읽기 오류] {error}")

def category_remove(service: TransactionService) -> None:
    category_name = input("삭제할 카테고리명: ").strip()

    try:
        service.category_remove(category_name)
    except ValueError as error:
        print(f"[에러] {error}")
    except OSError as error:
        print(f"[파일 처리 오류] {error}")
    else:
        print(f"[삭제 완료] {category_name}")

def export_data(
        service: TransactionService,
        out_path: str,
        date_month: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
) -> None:
    try:
        count = service.export_transaction_service(
            out_path=out_path,
            date_month=date_month,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as error:
        print(f"[입력 또는 데이터 오류] {error}")
    except OSError as error:
        print(f"[파일 저장 오류] {error}")
    else:
        print(f"[내보내기 완료] {count}건 → {out_path}")


def main():
    parser = build_parser()
    args = parser.parse_args()
    repository = TransactionRepository()
    category_repository = CategoryRepository()
    budget_repository = BudgetRepository()
    service = TransactionService(repository, category_repository, budget_repository)

    if args.command == "add":
        add_transactions(service=service)
    elif args.command == "list":
        list_transactions(service=service, limit=args.limit)
    elif args.command == "update":
        update_transactions(service=service, args_id=args.id)
    elif args.command == "delete":
        delete_transactions(service=service, args_id=args.id)
    elif args.command == "search":
        search_transactions(service=service, date_from=args.date_from, date_to=args.date_to, category=args.category, search_type=args.type, memo=args.q, tag=args.tags)
    elif args.command == "summary":
        summary_transactions(service=service, date_month=args.date_month, top_n=args.top_n)
    elif args.command == "budget":
        if args.budget_command == "set":
            budget_transactions(service=service, date_month=args.date_month, amount=args.amount)
    elif args.command == "category":
        if args.category_command == "add":
            category_add(service=service)
        elif args.category_command == "list":
            category_list(service=service)
        elif args.category_command == "remove":
            category_remove(service=service)
    elif args.command == "export":
        export_data(service=service, out_path=args.export_out, date_month=args.export_month, date_from=args.export_month_from, date_to=args.export_month_to)


