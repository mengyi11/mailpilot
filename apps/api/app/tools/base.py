from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session


InputT = TypeVar("InputT", bound=BaseModel)


class ToolExecutionError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class ToolContext:
    user_id: UUID
    permissions: frozenset[str]
    trace_id: str


class BaseTool(ABC, Generic[InputT]):
    name: str
    description: str
    permission: str
    input_model: type[InputT]

    def parse_input(self, arguments: dict[str, Any]) -> InputT:
        return self.input_model.model_validate(arguments)

    def authorize(self, context: ToolContext) -> None:
        if self.permission not in context.permissions:
            raise ToolExecutionError(
                "TOOL_PERMISSION_DENIED",
                f"Permission {self.permission} is required for {self.name}.",
            )

    @abstractmethod
    async def execute(
        self, db: Session, context: ToolContext, arguments: InputT
    ) -> dict[str, Any] | list[Any]:
        raise NotImplementedError
