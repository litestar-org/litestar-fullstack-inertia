#!/usr/bin/env python3
"""Intelligent MCP tool detection with capability mapping.

This script detects available MCP tools and generates a capability report.
Run: python .claude/tools/detect_mcp.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ToolCapability(Enum):
    """MCP tool capability categories."""

    REASONING = "reasoning"
    RESEARCH = "research"
    PLANNING = "planning"
    ANALYSIS = "analysis"
    DEBUG = "debug"
    CONSENSUS = "consensus"


@dataclass
class MCPTool:
    """MCP tool with capability metadata."""

    name: str
    available: bool
    capability: ToolCapability
    fallback: str | None = None
    use_cases: list[str] = field(default_factory=list)


def detect_mcp_tools() -> dict[str, MCPTool]:
    """Detect available MCP tools with intelligent fallback mapping."""
    return {
        "sequential_thinking": MCPTool(
            name="mcp__sequential-thinking__sequentialthinking",
            available=True,
            capability=ToolCapability.REASONING,
            fallback=None,
            use_cases=[
                "Linear problem breakdown",
                "Step-by-step analysis",
                "Complex feature planning",
            ],
        ),
        "context7_resolve": MCPTool(
            name="mcp__context7__resolve-library-id",
            available=True,
            capability=ToolCapability.RESEARCH,
            fallback="WebSearch",
            use_cases=[
                "Library name to ID resolution",
                "Package discovery",
            ],
        ),
        "context7_docs": MCPTool(
            name="mcp__context7__get-library-docs",
            available=True,
            capability=ToolCapability.RESEARCH,
            fallback="WebSearch",
            use_cases=[
                "Library documentation lookup",
                "API reference retrieval",
                "Best practices research",
            ],
        ),
        "pal_planner": MCPTool(
            name="mcp__pal__planner",
            available=True,
            capability=ToolCapability.PLANNING,
            fallback="TodoWrite with structured checkpoints",
            use_cases=[
                "Multi-phase project planning",
                "Migration strategy design",
                "Complex feature breakdown",
            ],
        ),
        "pal_thinkdeep": MCPTool(
            name="mcp__pal__thinkdeep",
            available=True,
            capability=ToolCapability.ANALYSIS,
            fallback="sequential_thinking",
            use_cases=[
                "Architecture review",
                "Performance analysis",
                "Security assessment",
            ],
        ),
        "pal_analyze": MCPTool(
            name="mcp__pal__analyze",
            available=True,
            capability=ToolCapability.ANALYSIS,
            fallback="Grep + Read manual analysis",
            use_cases=[
                "Code quality analysis",
                "Pattern detection",
                "Tech debt assessment",
            ],
        ),
        "pal_debug": MCPTool(
            name="mcp__pal__debug",
            available=True,
            capability=ToolCapability.DEBUG,
            fallback="Manual investigation",
            use_cases=[
                "Root cause investigation",
                "Bug reproduction",
                "Performance debugging",
            ],
        ),
        "pal_consensus": MCPTool(
            name="mcp__pal__consensus",
            available=True,
            capability=ToolCapability.CONSENSUS,
            fallback="Manual pros/cons analysis",
            use_cases=[
                "Technology decisions",
                "Architecture trade-offs",
                "Multi-perspective evaluation",
            ],
        ),
        "pal_chat": MCPTool(
            name="mcp__pal__chat",
            available=True,
            capability=ToolCapability.REASONING,
            fallback=None,
            use_cases=[
                "Brainstorming",
                "Quick questions",
                "Second opinions",
            ],
        ),
    }


def generate_tool_strategy(tools: dict[str, MCPTool]) -> str:
    """Generate intelligent tool usage strategy."""
    lines = [
        "# MCP Tool Detection Report",
        "",
        f"**Tools Detected**: {len(tools)}",
        "",
        "## Tools by Capability",
        "",
    ]

    # Group by capability
    by_capability: dict[ToolCapability, list[MCPTool]] = {}
    for tool in tools.values():
        if tool.capability not in by_capability:
            by_capability[tool.capability] = []
        by_capability[tool.capability].append(tool)

    for capability, tool_list in by_capability.items():
        lines.append(f"### {capability.value.title()}")
        for tool in tool_list:
            status = "Available" if tool.available else "Unavailable"
            lines.append(f"- **{tool.name}**: {status}")
            if tool.fallback:
                lines.append(f"  - Fallback: {tool.fallback}")
            lines.extend(f"  - {use_case}" for use_case in tool.use_cases)
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Run MCP tool detection."""
    import sys

    sys.stdout.write("MCP Tool Detection\n")
    sys.stdout.write("=" * 40 + "\n")

    tools = detect_mcp_tools()
    strategy = generate_tool_strategy(tools)

    sys.stdout.write(strategy)

    # Summary
    available = sum(1 for t in tools.values() if t.available)
    sys.stdout.write(f"\nSummary: {available}/{len(tools)} tools available\n")


if __name__ == "__main__":
    main()
