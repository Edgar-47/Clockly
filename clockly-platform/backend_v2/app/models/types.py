from enum import StrEnum

from sqlalchemy import Enum


def enum_column(enum_cls: type[StrEnum], *, name: str, length: int = 32) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        length=length,
        values_callable=lambda values: [item.value for item in values],
    )

