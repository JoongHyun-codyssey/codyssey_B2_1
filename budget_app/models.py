from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Transaction:
    id: str
    date: str
    type: Literal["income", "expense"]
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)