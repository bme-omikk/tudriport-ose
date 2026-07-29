from dataclasses import dataclass

@dataclass
class ScoringToken:
    token: str
    score: float
    description: str
    summable: bool = True
