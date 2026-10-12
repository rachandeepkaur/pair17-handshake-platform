from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


def clean_optional_text(value: str | None) -> str | None:
    """Trim free-text input and store blank strings as NULL."""

    if value is None:
        return None
    value = value.strip()
    return value or None


def clean_required_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("This field cannot be empty")
    return value
