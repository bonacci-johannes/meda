from dataclasses import dataclass
from typing import Set


@dataclass
class BooleanCases:
    true: Set[str]
    false: Set[str]
    null: Set[str]
