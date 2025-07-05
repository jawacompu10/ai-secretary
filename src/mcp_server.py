"""
Main MCP server entry point for the Secretary application.

This module serves as the central entry point for the Model Context Protocol (MCP) server,
providing calendar and task management tools to AI clients.
"""

import sys
from pathlib import Path

# Add project root to Python path when running directly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.tools.calendar_tools import calendar_mcp

if __name__ == "__main__":
    calendar_mcp.run(transport="stdio")