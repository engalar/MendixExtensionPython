"""
Pydantic input models for DSL generation tools.

All models use alias support for JSON deserialization from MCP clients.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class DSLFormatOptions(BaseModel):
    """Output format configuration for DSL generation"""
    model_config = {"populate_by_name": True}

    include_documentation: bool = Field(
        True, alias="IncludeDocumentation",
        description="Include element documentation/comments in output"
    )
    include_location: bool = Field(
        False, alias="IncludeLocation",
        description="Include diagram position coordinates (for visual elements)"
    )
    detail_level: Literal["brief", "standard", "detailed"] = Field(
        "standard", alias="DetailLevel",
        description="Level of detail in generated DSL"
    )


class DomainModelDSLInput(BaseModel):
    """Input for generating domain model DSL"""
    model_config = {"populate_by_name": True}

    module_name: str = Field(
        ..., alias="ModuleName",
        description="Name of the module to analyze"
    )
    entity_names: Optional[List[str]] = Field(
        None, alias="EntityNames",
        description="Optional list of specific entities to include (null = all)"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions"
    )


class MicroflowDSLInput(BaseModel):
    """Input for generating microflow DSL"""
    model_config = {"populate_by_name": True}

    qualified_name: str = Field(
        ..., alias="QualifiedName",
        description="Qualified name (Module.MicroflowName)"
    )
    include_expressions: bool = Field(
        True, alias="IncludeExpressions",
        description="Include microflow expression details"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions"
    )


class PageDSLInput(BaseModel):
    """Input for generating page DSL"""
    model_config = {"populate_by_name": True}

    qualified_name: str = Field(
        ..., alias="QualifiedName",
        description="Qualified name (Module.PageName or Module.Folder.PageName)"
    )
    include_widget_properties: bool = Field(
        False, alias="IncludeWidgetProperties",
        description="Include detailed widget property values"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions"
    )


class WorkflowDSLInput(BaseModel):
    """Input for generating workflow DSL (Mendix 9.24+ workflows)"""
    model_config = {"populate_by_name": True}

    qualified_name: str = Field(
        ..., alias="QualifiedName",
        description="Qualified name (Module.WorkflowName)"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions"
    )


class ModuleTreeDSLInput(BaseModel):
    """Input for generating module file/folder tree DSL"""
    model_config = {"populate_by_name": True}

    module_name: str = Field(
        ..., alias="ModuleName",
        description="Name of the module"
    )
    include_system_elements: bool = Field(
        False, alias="IncludeSystemElements",
        description="Include system-generated elements in tree"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions"
    )


class JavaActionDSLInput(BaseModel):
    """Input for generating JavaAction DSL for a module."""
    model_config = {"populate_by_name": True}

    module_name: str = Field(
        ..., alias="ModuleName",
        description="Name of the module to analyze"
    )
    format_options: DSLFormatOptions = Field(
        default_factory=DSLFormatOptions, alias="FormatOptions",
        description="Output format configuration"
    )
