"""
Main MCP server entry point for the Secretary application.

This module serves as the default entry point. By default, it runs the task server
since task management is the most commonly used functionality.

For specific servers, run:
- python src/servers/task_server.py        # Task management
- python src/servers/calendar_server.py    # Calendar administration  
- python src/servers/event_server.py       # Event scheduling (coming soon)
"""

import sys
from pathlib import Path

# Add project root to Python path when running directly
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.servers.task_server import task_mcp

if __name__ == "__main__":
    print("Starting Task Management MCP Server...")
    print("For other servers, run:")
    print("  - python src/servers/calendar_server.py (calendar management)")
    print("  - python src/servers/event_server.py (event scheduling)")
    task_mcp.run(transport="stdio")