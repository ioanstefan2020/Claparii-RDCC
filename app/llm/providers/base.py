from typing import Any, Protocol, Type

from pydantic import BaseModel


class Provider(Protocol):
    async def call(
        self, system: str, user: str, schema: Type[BaseModel], model: str, timeout: int
    ) -> dict[str, Any]: ...
