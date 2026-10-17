from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable, Generic, Mapping, Protocol, TypeVar

from pydantic import BaseModel


InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class FailureStrategy(StrEnum):
    FAIL_CLOSED = "fail_closed"
    RETURN_EMPTY = "return_empty"
    USE_ORIGINAL = "use_original"


class SkillExecutor(Protocol):
    async def execute(
        self,
        *,
        skill_name: str,
        prompt: str,
        payload: Mapping[str, Any],
        output_schema: type[BaseModel],
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class SkillDefinition(Generic[InputT, OutputT]):
    name: str
    prompt_version: str
    description: str
    prompt: str
    input_schema: type[InputT]
    output_schema: type[OutputT]
    allowed_tools: tuple[str, ...]
    failure_strategy: FailureStrategy
    max_attempts: int = 2
    fallback_factory: Callable[[InputT], Mapping[str, Any]] | None = None

    async def run(
        self,
        payload: InputT | Mapping[str, Any],
        executor: SkillExecutor,
    ) -> OutputT:
        validated_input = self.input_schema.model_validate(payload)
        last_error: Exception | None = None
        for _ in range(self.max_attempts):
            try:
                raw_output = await executor.execute(
                    skill_name=self.name,
                    prompt=self.prompt,
                    payload=validated_input.model_dump(mode="json"),
                    output_schema=self.output_schema,
                )
                return self.output_schema.model_validate(raw_output)
            except Exception as exc:  # executor and schema failures share one retry budget
                last_error = exc
        assert last_error is not None
        if self.failure_strategy is not FailureStrategy.FAIL_CLOSED:
            if self.fallback_factory is None:
                raise RuntimeError(f"{self.name} has no fallback factory") from last_error
            return self.output_schema.model_validate(self.fallback_factory(validated_input))
        raise last_error

