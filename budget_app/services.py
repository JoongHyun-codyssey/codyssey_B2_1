from typing import Literal
from typing import Optional

def add():
    print("add123")

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