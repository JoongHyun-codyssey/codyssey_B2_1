# Budget App — Python 콘솔 가계부

Python으로 구현하는 파일 입출력 기반 콘솔 가계부입니다. 수입과 지출을 기록하고, 검색·월별 요약·예산 관리 기능을 통해 거래 내역을 관리합니다.

> 현재 프로젝트 구조를 설계하는 단계입니다. 아래 기능과 명령어는 구현 목표이며, 실제 구현에 맞춰 갱신할 예정입니다. CSV 세부 스키마는 제공된 과제 내용에 누락되어 있어 아래에 임시 설계안을 작성했습니다.

## 1. 학습 목표

- JSONL 파일 기반 데이터 영구 저장과 CRUD 구현
- 모델·저장소·서비스·CLI의 역할 분리
- `yield` 기반 제너레이터를 이용한 파일 스트리밍 처리
- 데코레이터를 이용한 로그·예외 처리·실행 시간 측정 분리
- 타입 힌트와 `dataclass`를 활용한 데이터 구조 및 입출력 계약 명확화

## 2. 주요 기능

- [ ] 거래 추가: 대화형 입력 및 고유 ID 생성
- [ ] 거래 목록: 최신순 조회 및 출력 개수 제한
- [ ] 거래 검색: 기간, 카테고리, 타입, 메모, 태그 조건 검색
- [ ] 거래 수정: ID 기반 옵션 방식으로 지정한 필드만 수정
- [ ] 거래 삭제: ID 기반 삭제 및 없는 ID 안내
- [ ] 월별 요약: 총수입·총지출·잔액 및 카테고리별 지출 TOP N
- [ ] 예산 설정·조회: 월별 예산 저장 및 사용률·초과 경고
- [ ] 카테고리 관리: 추가·목록·삭제 및 사용 중인 카테고리 삭제 방지
- [ ] CSV 가져오기·내보내기: 일괄 등록 및 조건별 내보내기
- [ ] 입력 검증, 예외 처리, 실행 로그, 실행 시간 측정

## 3. 프로젝트 구조

```text
budget-project/
├── budget_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py
│   ├── storage.py
│   └── services.py
├── data/
│   ├── transactions.jsonl
│   ├── categories.jsonl
│   └── budgets.jsonl
├── README.md
└── .gitignore
```

| 파일 | 역할 |
| --- | --- |
| `__init__.py` | 패키지 초기화 파일. 초기에는 빈 파일로 유지 |
| `__main__.py` | 실행 진입점, 명령어·옵션 해석, 대화형 입력 및 결과 출력 |
| `models.py` | `Transaction` 등 데이터 클래스 정의 |
| `storage.py` | 저장소 클래스, 파일 읽기·쓰기, 제너레이터, 안전한 파일 교체 |
| `services.py` | 입력 검증, 거래·카테고리·예산 관리, 요약, CSV 처리 |
| `data/` | 프로그램 종료 후에도 유지되는 데이터 저장 폴더 |

최소 `Transaction`과 `TransactionRepository` 클래스를 사용합니다. 데코레이터는 우선 `services.py`에 정의하고, 여러 모듈에서 필요해지면 별도 파일로 분리할 예정입니다.

## 4. 실행 방법

Python 3.10 이상을 개발 기준으로 사용하며, 초기 구현은 표준 라이브러리만 사용할 예정입니다. 실제 검증한 Python 버전은 구현 후 추가합니다.

프로젝트 최상위 폴더에서 실행합니다.

```bash
python -m budget_app --help
python -m budget_app add
```

환경에 따라 `python` 대신 `python3`를 사용합니다. 모든 명령 및 하위 명령에서 `--help`를 지원하도록 구현합니다.

저장 폴더 변경 옵션은 명령어 앞에 지정합니다.

```bash
python -m budget_app --data-dir ./custom-data list
```

## 5. 주요 명령 예시

아래는 구현 예정 인터페이스입니다. `<id>`는 실제 거래 ID로 바꿉니다.

```bash
# 거래 추가: 날짜, 타입, 카테고리, 금액, 메모, 태그를 순서대로 입력
python -m budget_app add

# 거래 목록: 기본 10건
python -m budget_app list --limit 10

# 조건 검색: 함께 지정한 조건은 모두 만족해야 함
python -m budget_app search --from 2026-09-01 --to 2026-09-30
python -m budget_app search --category food --type expense
python -m budget_app search --q 점심 --tag 외식

# 거래 수정: 옵션 방식으로 고정, 생략한 필드는 유지
python -m budget_app update --id <id> --amount 12000 --memo "점심 식사"

# 거래 삭제
python -m budget_app delete --id <id>

# 월별 요약: TOP 기본 5개
python -m budget_app summary --month 2026-09 --top 5

# 월별 예산 설정 및 조회
python -m budget_app budget set --month 2026-09 --amount 500000
python -m budget_app budget show --month 2026-09

# 카테고리 관리: 추가·삭제할 이름은 대화형으로 입력
python -m budget_app category add
python -m budget_app category list
python -m budget_app category remove

# CSV 가져오기
python -m budget_app import --from ./transactions.csv

# CSV 내보내기: 월 또는 시작일·종료일 쌍 중 하나를 필수 지정
python -m budget_app export --out ./september.csv --month 2026-09
python -m budget_app export --out ./period.csv --from 2026-09-01 --to 2026-09-15
```

`update`는 `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`를 지원할 예정입니다. 메모는 `--memo ""`, 태그는 `--tags ""`로 비우며, 태그가 여러 개이면 `--tags "외식;점심"`처럼 입력합니다.

## 6. 데이터 저장 형식

기본 저장 위치는 실행한 작업 디렉터리 기준 `./data`입니다. 파일과 폴더가 없으면 첫 실행 시 자동 생성합니다. 저장 형식은 JSONL로 통일하며, 한 줄에 하나의 JSON 객체를 저장합니다.

### 거래: `transactions.jsonl`

```json
{"id":"example-id-001","type":"expense","date":"2026-09-17","amount":10000,"category":"food","memo":"점심","tags":["외식"]}
```

| 필드 | 형식 및 규칙 |
| --- | --- |
| `id` | 고유 문자열, 신규 거래 생성 시 UUID 사용 예정 |
| `type` | `income` 또는 `expense` |
| `date` | 실제 존재하는 날짜, `YYYY-MM-DD` |
| `amount` | 원 단위 양의 정수 |
| `category` | 등록된 카테고리 이름 |
| `memo` | 문자열, 기본값은 빈 문자열 |
| `tags` | 문자열 목록, 기본값은 빈 목록 |

### 카테고리: `categories.jsonl`

```json
{"name":"food"}
{"name":"salary"}
```

빈 카테고리 파일에는 `food`, `transport`, `rent`, `salary`, `etc`를 기본 생성하는 정책으로 구현할 예정입니다. 거래에서 사용 중인 카테고리의 삭제는 차단합니다.

### 예산: `budgets.jsonl`

```json
{"month":"2026-09","amount":500000}
```

예산 금액은 양의 정수이며, 같은 월에 다시 설정하면 기존 예산을 갱신합니다. 사용률은 `해당 월 총지출 / 예산 × 100`으로 계산합니다. 지출이 예산보다 클 때 초과 경고를 표시하며, 거래가 없는 달은 데이터 없음을 명시합니다.

## 7. CSV import/export 스키마 — 임시 설계안

> 과제 원문에 명시된 최소 CSV 스키마를 확인한 뒤 아래 설계와 대조하여 확정해야 합니다.

UTF-8 인코딩을 사용하며, 첫 줄에 다음 헤더를 포함합니다. 한글 스프레드시트 호환을 위해 UTF-8 BOM도 읽을 수 있도록 구현할 예정입니다.

```csv
id,type,date,amount,category,memo,tags
example-id-001,expense,2026-09-17,10000,food,점심,외식;점심
example-id-002,income,2026-09-17,2500000,salary,월급,
```

- 헤더는 위 7개 열로 고정하며, `memo`와 `tags`의 값은 비워도 됩니다.
- `tags`는 세미콜론(`;`)으로 구분합니다. 개별 태그 내부의 세미콜론은 허용하지 않습니다.
- 쉼표·줄바꿈·따옴표가 포함된 값은 Python `csv` 모듈의 CSV 인용 규칙에 따라 처리합니다.
- 가져올 때 `id`가 비어 있으면 새 ID를 생성합니다. 값이 있으면 유지하되, 기존 데이터 및 입력 CSV 내부의 중복 ID는 오류로 처리합니다.
- 등록되지 않은 카테고리, 잘못된 날짜·금액·타입이 있으면 행 번호와 오류를 안내합니다.
- 가져오기는 전체 입력 검증을 통과한 경우에만 반영하여 부분 저장을 방지할 예정입니다.
- 내보내기는 `--month` 또는 `--from`과 `--to` 쌍을 선택하며, 두 방식을 동시에 사용하지 않습니다. 날짜 경계는 포함합니다.
- 성공 시 가져온 건수 또는 내보낸 건수와 출력 경로를 표시합니다.

## 8. 데이터 안전성과 구현 방침

- 파일은 `yield` 기반 제너레이터로 한 줄씩 읽고 처리합니다.
- 수정·삭제는 같은 폴더의 임시 파일에 결과를 기록한 뒤 `os.replace()`로 교체합니다. 기록 중 실패하면 원본을 유지하도록 설계합니다.
- 읽기 중 손상된 JSON이나 잘못된 저장 데이터를 만나면 위치를 안내하고 중단합니다. 손상된 행을 조용히 누락한 채 재저장하지 않습니다.
- 날짜·금액·타입·카테고리를 검증하고, 존재하지 않는 ID는 사용자 메시지로 처리합니다.
- 예외 처리는 CLI 경계에서 사용자에게 안내하고, 저장 계층의 실패를 성공으로 처리하지 않습니다.
- 여러 프로세스의 동시 쓰기는 초기 지원 범위에서 제외하며, 한 번에 한 프로세스만 실행하는 것을 전제로 합니다.

### 최신순과 스트리밍

최신순의 기준은 거래 날짜 내림차순으로 정하고, 같은 날짜에서는 ID로 순서를 고정할 예정입니다. 파일에 추가된 순서가 거래 날짜순이라는 가정은 하지 않습니다.

`list --limit N`은 파일을 순회하면서 최신 N건만 보관하는 방식을 검토합니다. 검색 결과 전체를 최신순으로 출력하는 방법은 구현 전 확정할 항목입니다. 단순히 `sorted()`로 결과 전체를 메모리에 모으는 방식은 엄격한 스트리밍 요구를 충족하지 못하므로, 날짜순 저장 유지 또는 외부 정렬 같은 방식을 검토합니다.

## 9. 검증 계획

- [ ] 재실행 후 거래·카테고리·예산 데이터 유지
- [ ] 잘못된 날짜, 0·음수 금액, 잘못된 타입 및 미등록 카테고리 처리
- [ ] 존재하지 않는 ID 수정·삭제 처리
- [ ] 사용 중인 카테고리 삭제 차단
- [ ] 데이터 없는 달의 요약 및 예산 초과 경고
- [ ] 최신순 정렬, 검색 조건 조합 및 출력 개수 제한
- [ ] CSV 중복 ID·잘못된 행 검증 및 import/export 왕복 확인
- [ ] 파일 기록 실패 시 원본 데이터 보존
- [ ] 모든 명령의 `--help` 및 `--data-dir` 동작 확인

구현이 진행되면 완료한 항목을 체크하고, 실제 실행 결과와 테스트 방법을 추가합니다.
