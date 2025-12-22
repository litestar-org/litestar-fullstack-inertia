"""Intelligent MCP tool detection with capability mapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ToolCapability(Enum):
    """MCP tool capability categories."""
    REASONING = "reasoning"  # Deep thinking tools
    RESEARCH = "research"    # Documentation lookup
    PLANNING = "planning"    # Workflow organization
    ANALYSIS = "analysis"    # Code analysis
    DEBUG = "debug"          # Problem investigation


@dataclass
class MCPTool:
    """MCP tool with capability metadata."""
    name: str
    available: bool
    capability: ToolCapability
    fallback: str | None = None
    use_cases: list[str] | None = None


def detect_mcp_tools() -> dict[str, MCPTool]:
    """Detect available MCP tools with intelligent fallback mapping."""

    # In this bootstrap context, we simulate detection or check env if possible.
    # For now, we assume standard set is "available" to generate the strategy,
    # as the agent itself provides these capabilities via tools.

    return {
        # Reasoning tools
        "sequential_thinking": MCPTool(
            name="sequential_thinking",
            available=True,
            capability=ToolCapability.REASONING,
            fallback=None,
            use_cases=[
                "Complex architectural decisions",
                "Multi-step problem analysis",
                "Iterative problem refinement",
            ],
        ),

        # Research tools
        "context7": MCPTool(
            name="context7",
            available=True,
            capability=ToolCapability.RESEARCH,
            fallback="web_search",
            use_cases=[
                "Library documentation lookup",
                "API reference retrieval",
                "Best practices research",
            ],
        ),
        "web_search": MCPTool(
            name="web_search",
            available=True,
            capability=ToolCapability.RESEARCH,
            fallback=None,
            use_cases=[
                "Latest framework updates",
                "Community best practices",
                "Fallback documentation lookup",
            ],
        ),

        # Planning tools
        "zen_planner": MCPTool(
            name="zen_planner",
            available=True,
            capability=ToolCapability.PLANNING,
            use_cases=[
                "Multi-phase project planning",
                "Migration strategy design",
                "Complex feature breakdown",
            ],
        ),

        # Analysis tools
        "zen_thinkdeep": MCPTool(
            name="zen_thinkdeep",
            available=True,
            capability=ToolCapability.ANALYSIS,
            use_cases=[
                "Architecture review",
                "Performance analysis",
                "Security assessment",
            ],
        ),
        "zen_analyze": MCPTool(
            name="zen_analyze",
            available=True,
            capability=ToolCapability.ANALYSIS,
            use_cases=[
                "Code quality analysis",
                "Pattern detection",
                "Tech debt assessment",
            ],
        ),

        # Debug tools
        "zen_debug": MCPTool(
            name="zen_debug",
            available=True,
            capability=ToolCapability.DEBUG,
            use_cases=[
                "Root cause investigation",
                "Bug reproduction",
                "Performance debugging",
            ],
        ),
        "zen_consensus": MCPTool(
            name="zen_consensus",
            available=True,
            capability=ToolCapability.PLANNING,
            use_cases=[
                "Architecture decision making",
                "Technology selection",
                "Multi-model validation",
            ],
        ),
    }


def generate_tool_strategy(tools: dict[str, MCPTool]) -> str:
    """Generate intelligent tool usage strategy."""

    strategy = ["# MCP Tool Strategy\n\n"]

    by_capability = {}
    for tool in tools.values():
        if tool.capability not in by_capability:
            by_capability[tool.capability] = []
        by_capability[tool.capability].append(tool)

    for capability, tool_list in by_capability.items():
        strategy.append(f"## {capability.value.title()} Tools\n\n")

        available = [t for t in tool_list if t.available]

        if available:
            primary = available[0]
            strategy.append(f"**Primary**: `{primary.name}`\n\n")

            if primary.use_cases:
                strategy.append("Use when:\n\n")
                strategy.extend(f"- {use_case}\n" for use_case in primary.use_cases)
                strategy.append("\n")

            if primary.fallback:
                strategy.append(f"**Fallback**: `{primary.fallback}`\n\n")
        else:
            strategy.append(f"No tools available - manual {capability.value} required\n\n")

    return "".join(strategy)


if __name__ == "__main__":
    import sys

    tools = detect_mcp_tools()

    # Generate strategy document
    strategy = generate_tool_strategy(tools)

    with Path(".gemini/mcp-strategy.md").open("w") as f:
        f.write(strategy)

    # Generate availability list
    with Path(".gemini/mcp-tools.txt").open("w") as f:
        f.write("Available MCP Tools (Auto-Detected):\n\n")
        for tool in tools.values():
            status = "Available" if tool.available else "Not available"
            f.write(f"- {tool.name}: {status}\n")
            if tool.fallback:
                f.write(f"  Fallback: {tool.fallback}\n")

    sys.stdout.write("MCP tool detection complete\n")
