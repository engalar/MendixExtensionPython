from typing import Annotated
from pydantic import BaseModel, Field

from ..tool_registry import mcp


class ShrimpTank(BaseModel):
    """A model for a shrimp tank"""
    class Shrimp(BaseModel):
        """A model for a shrimp"""
        name: Annotated[str, Field(max_length=10, description="Shrimp name")]

    shrimp: Annotated[list[Shrimp], Field(description="Shrimp list")]


class ShrimpTankToolInput(BaseModel):
    """A model for a shrimp tank tool input"""
    tank: Annotated[ShrimpTank, Field(description="Shrimp tank")]
    extra_names: Annotated[list[str], Field(description="Extra names")]


class ShrimpTankToolOutput(BaseModel):
    """A model for a shrimp tank tool output"""
    tank: Annotated[list[str], Field(description="Shrimp list")]


@mcp.tool(description="A tool that takes a shrimp tank and returns the name of the shrimp")
def name_shrimp(
    request: ShrimpTankToolInput
) -> ShrimpTankToolOutput:
    return [shrimp.name for shrimp in request.tank.shrimp] + request.extra_names


"""
{
  "shrimp": [
    {"name": "Nemo"},
    {"name": "Dory"},
    {"name": "Bubbles"}
  ]
}

[
  "b1",
  "b2"
]
"""
