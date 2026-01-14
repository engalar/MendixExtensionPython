"""
MCP Tools and Resources for DSL generation.

This module provides both Tool (on-demand) and Resource (URL-based)
endpoints for generating DSL representations of Mendix models.
"""

from .. import mendix_context as ctx
from ..tool_registry import mcp
import importlib

# Import business logic and DTOs
from pymx.model import dsl
importlib.reload(dsl)
from pymx.model.dto import type_dsl
importlib.reload(type_dsl)

# ==========================================
# DSL TOOLS (On-demand generation)
# ==========================================


@mcp.tool(
    name="generate_domain_model_dsl",
    description="Generate human-readable DSL documentation for entities, attributes, and associations in a module"
)
async def tool_domain_model_dsl(data: type_dsl.DomainModelDSLInput) -> str:
    """
    Generate DomainModel DSL for a module.

    Args:
        data: DomainModelDSLInput with module name and format options

    Returns:
        DSL string showing entities, attributes, associations, and inheritance
    """
    return dsl.generate_domain_model_dsl(ctx.CurrentApp, data)


@mcp.tool(
    name="generate_microflow_dsl",
    description="Generate ASCII art flow visualization for a microflow with activity details"
)
async def tool_microflow_dsl(data: type_dsl.MicroflowDSLInput) -> str:
    """
    Generate Microflow DSL with activity flow visualization.

    Args:
        data: MicroflowDSLInput with qualified name and expression options

    Returns:
        DSL string showing microflow parameters, return type, and activity flow
    """
    return dsl.generate_microflow_dsl(ctx.CurrentApp, data)


@mcp.tool(
    name="generate_page_dsl",
    description="Generate widget tree structure DSL for a page"
)
async def tool_page_dsl(data: type_dsl.PageDSLInput) -> str:
    """
    Generate Page DSL showing widget hierarchy.

    Args:
        data: PageDSLInput with qualified name and property options

    Returns:
        DSL string with nested widget tree structure
    """
    return dsl.generate_page_dsl(ctx.CurrentApp, data)


@mcp.tool(
    name="generate_workflow_dsl",
    description="Generate activity flow DSL for a workflow (Mendix 9.24+)"
)
async def tool_workflow_dsl(data: type_dsl.WorkflowDSLInput) -> str:
    """
    Generate Workflow DSL with user tasks and flow visualization.

    Args:
        data: WorkflowDSLInput with qualified name

    Returns:
        DSL string showing workflow activities and decision points
    """
    return dsl.generate_workflow_dsl(ctx.CurrentApp, data)


@mcp.tool(
    name="generate_module_tree_dsl",
    description="Generate file/folder tree DSL for a module's structure"
)
async def tool_module_tree_dsl(data: type_dsl.ModuleTreeDSLInput) -> str:
    """
    Generate ModuleTree DSL showing folder and document structure.

    Args:
        data: ModuleTreeDSLInput with module name

    Returns:
        DSL string with ASCII tree of module contents
    """
    return dsl.generate_module_tree_dsl(ctx.CurrentApp, data)


@mcp.tool(
    name="generate_java_action_dsl",
    description="Generate human-readable DSL for all Java Actions in a module"
)
async def tool_java_action_dsl(data: type_dsl.JavaActionDSLInput) -> str:
    return dsl.generate_java_action_dsl(ctx.CurrentApp, data)


# ==========================================
# DSL RESOURCES (URL-based access)
# ==========================================

# Pattern: model://dsl/{type}/{qualified-name}.{ext}
# Extensions: .txt for text DSL, .md for markdown


@mcp.resource(
    "model://dsl/domain/{module_name}.mxdomain.txt",
    description="DomainModel DSL documentation for all entities in a module",
    mime_type="text/plain"
)
def resource_domain_model_dsl(module_name: str) -> str:
    """
    Generate DomainModel DSL for a module via resource URL.

    Example: model://dsl/domain/MyModule.mxdomain.txt

    使用scripts/test_mcp_studiopro.py进行测试
    """
    data = type_dsl.DomainModelDSLInput(ModuleName=module_name)
    return dsl.generate_domain_model_dsl(ctx.CurrentApp, data)


@mcp.resource(
    "model://dsl/microflow/{qualified_name}.mfmicroflow.txt",
    description="Microflow DSL with ASCII art flow visualization",
    mime_type="text/plain"
)
def resource_microflow_dsl(qualified_name: str) -> str:
    """
    Generate Microflow DSL via resource URL.

    Example: model://dsl/microflow/MyModule.MyMicroflow.mfmicroflow.txt
    """
    data = type_dsl.MicroflowDSLInput(QualifiedName=qualified_name)
    return dsl.generate_microflow_dsl(ctx.CurrentApp, data)


@mcp.resource(
    "model://dsl/page/{qualified_name}.mfpage.txt",
    description="Page DSL showing widget tree structure",
    mime_type="text/plain"
)
def resource_page_dsl(qualified_name: str) -> str:
    """
    Generate Page DSL via resource URL.

    Example: model://dsl/page/MyModule.MyPage.mfpage.txt
             model://dsl/page/MyModule.Pages.MyPage.mfpage.txt
    """
    data = type_dsl.PageDSLInput(QualifiedName=qualified_name)
    return dsl.generate_page_dsl(ctx.CurrentApp, data)


@mcp.resource(
    "model://dsl/workflow/{qualified_name}.mfworkflow.txt",
    description="Workflow DSL with activity flow visualization",
    mime_type="text/plain"
)
def resource_workflow_dsl(qualified_name: str) -> str:
    """
    Generate Workflow DSL via resource URL.

    Example: model://dsl/workflow/MyModule.MyWorkflow.mfworkflow.txt
    """
    data = type_dsl.WorkflowDSLInput(QualifiedName=qualified_name)
    return dsl.generate_workflow_dsl(ctx.CurrentApp, data)


@mcp.resource(
    "model://dsl/module/{module_name}.mfmodule.tree.txt",
    description="Module file/folder tree DSL",
    mime_type="text/plain"
)
def resource_module_tree_dsl(module_name: str) -> str:
    """
    Generate ModuleTree DSL via resource URL.

    Example: model://dsl/module/MyModule.mfmodule.tree.txt
    """
    data = type_dsl.ModuleTreeDSLInput(ModuleName=module_name)
    return dsl.generate_module_tree_dsl(ctx.CurrentApp, data)


@mcp.resource(
    "model://dsl/java_actions/{module_name}.mxjavaactions.txt",
    description="DSL for all Java Actions in a module",
    mime_type="text/plain"
)
def resource_java_action_dsl(module_name: str) -> str:
    data = type_dsl.JavaActionDSLInput(ModuleName=module_name)
    return dsl.generate_java_action_dsl(ctx.CurrentApp, data)


# ==========================================
# CONVENIENCE RESOURCES (Markdown format)
# ==========================================


@mcp.resource(
    "model://dsl/domain/{module_name}.md",
    description="DomainModel DSL in Markdown format",
    mime_type="text/markdown"
)
def resource_domain_model_md(module_name: str) -> str:
    """Generate DomainModel DSL formatted as Markdown"""
    dsl_content = resource_domain_model_dsl(module_name)
    return f"# Domain Model: {module_name}\n\n```\n{dsl_content}\n```"


@mcp.resource(
    "model://dsl/microflow/{qualified_name}.md",
    description="Microflow DSL in Markdown format",
    mime_type="text/markdown"
)
def resource_microflow_md(qualified_name: str) -> str:
    """Generate Microflow DSL formatted as Markdown"""
    dsl_content = resource_microflow_dsl(qualified_name)
    parts = qualified_name.split(".")
    module_name = parts[0] if len(parts) > 0 else "Unknown"
    mf_name = parts[-1] if len(parts) > 0 else "Unknown"
    return f"# Microflow: {mf_name}\n\n**Module:** {module_name}\n\n```\n{dsl_content}\n```"


@mcp.resource(
    "model://dsl/page/{qualified_name}.md",
    description="Page DSL in Markdown format",
    mime_type="text/markdown"
)
def resource_page_md(qualified_name: str) -> str:
    """Generate Page DSL formatted as Markdown"""
    dsl_content = resource_page_dsl(qualified_name)
    parts = qualified_name.split(".")
    module_name = parts[0] if len(parts) > 0 else "Unknown"
    page_name = parts[-1] if len(parts) > 0 else "Unknown"
    return f"# Page: {page_name}\n\n**Module:** {module_name}\n\n```\n{dsl_content}\n```"


@mcp.resource(
    "model://dsl/workflow/{qualified_name}.md",
    description="Workflow DSL in Markdown format",
    mime_type="text/markdown"
)
def resource_workflow_md(qualified_name: str) -> str:
    """Generate Workflow DSL formatted as Markdown"""
    dsl_content = resource_workflow_dsl(qualified_name)
    parts = qualified_name.split(".")
    module_name = parts[0] if len(parts) > 0 else "Unknown"
    wf_name = parts[-1] if len(parts) > 0 else "Unknown"
    return f"# Workflow: {wf_name}\n\n**Module:** {module_name}\n\n```\n{dsl_content}\n```"


@mcp.resource(
    "model://dsl/module/{module_name}.tree.md",
    description="Module tree DSL in Markdown format",
    mime_type="text/markdown"
)
def resource_module_tree_md(module_name: str) -> str:
    """Generate ModuleTree DSL formatted as Markdown"""
    dsl_content = resource_module_tree_dsl(module_name)
    return f"# Module Structure: {module_name}\n\n```\n{dsl_content}\n```"
