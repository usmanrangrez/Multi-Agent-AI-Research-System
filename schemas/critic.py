from pydantic import BaseModel


class CriticResult(BaseModel):
    approved: bool
    feedback: list[str]