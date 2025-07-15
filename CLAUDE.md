# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

### Dependencies and Package Management
- Uses **UV** package manager (not pip or Poetry)
- Install dependencies: `uv sync`
- Python 3.12+ required
- Dependencies managed through `pyproject.toml`

### Configuration Requirements
Create configuration files in project root:
```bash
touch settings.toml
touch .secrets.toml  # For sensitive data
```

Example `settings.toml`:
```toml
[default]
calendar_url = "http://localhost:5232"
calendar_username = "your-username"
calendar_password = "your-password"

[development]
debug = true
```

### Calendar Server Setup
Start the CalDAV server for local development:
```bash
python3 -m radicale --storage-filesystem-folder=~/.var/lib/radicale/collections --auth-type none
```

## Architecture Overview

### Three-Server MCP Architecture
The project implements **Model Context Protocol (MCP)** servers with clear separation of concerns:

1. **Task Server** (`src/servers/task_server.py`) - Task lifecycle management
2. **Calendar Server** (`src/servers/calendar_server.py`) - Calendar administration 
3. **Event Server** (`src/servers/event_server.py`) - Event scheduling (placeholder)

Run servers individually:
```bash
python src/servers/task_server.py      # Most commonly used
python src/servers/calendar_server.py  # Calendar management
python src/servers/event_server.py     # Future events
```

### Provider Pattern Implementation
- **Protocol-based design**: `CalendarProvider` protocol in `src/providers/base.py`
- **CalDAV implementation**: `CalDavService` in `src/providers/caldav.py` 
- **Extensible**: Easy to add Google Calendar, Microsoft Graph providers
- **Helper methods**: Centralized calendar/task lookup to avoid code duplication

### Data Models (Pydantic)
Located in `src/core/models.py`:
- **Task**: Core task representation with calendar_name field
- **TaskCreate**: For creating new tasks with validation
- **TaskUpdate**: For modifying task due dates
- **TaskComplete**: For marking tasks complete

### Key Design Principles
1. **Multi-role support**: Designed for users juggling multiple calendars (Work, Personal, Projects)
2. **Calendar-centric operations**: All task operations require specifying calendar_name
3. **Protocol-based providers**: CalendarProvider protocol allows multiple backend implementations
4. **Pydantic validation**: MCP tools use Pydantic models for clean parameter handling
5. **Clean Code principles**: Follow Bob Martin's Clean Code guidelines - keep functions small, focused, and with descriptive names. Extract complex logic into separate functions with single responsibilities.

## Running MCP Servers

### Default Entry Points
```bash
python src/mcp_server.py              # Runs task server by default
python src/servers/task_server.py     # Direct task server
python src/servers/calendar_server.py # Direct calendar server
```

### Key MCP Tools Available

**Task Server Tools:**
- `get_tasks(include_completed=False, calendar_name=None)` - Filter by calendar
- `add_task(task_data: TaskCreate)` - Create tasks with calendar specification
- `edit_due_date(task_update: TaskUpdate)` - Modify task deadlines
- `complete_task(task_complete: TaskComplete)` - Mark tasks done

**Calendar Server Tools:**
- `get_all_calendar_names()` - List available calendars
- `create_new_calendar(name: str)` - Create new calendars for different roles

## Configuration System

Uses **Dynaconf** for environment-aware configuration:
- `config.py` at project root handles setup
- Calendar connection details required: `calendar_url`, `calendar_username`, `calendar_password`
- Supports multiple environments (development, production)
- Configuration validation with helpful error messages

## Multi-Calendar Workflow

The system is designed for users with multiple roles/contexts:
- **Work Calendar**: Professional tasks and meetings
- **Personal Calendar**: Personal tasks and appointments  
- **Project Calendars**: Specific project organization

Tasks always include `calendar_name` field to maintain context separation. Use `get_tasks(calendar_name="Work")` to focus on specific contexts.

## Key Files to Understand

- `src/providers/caldav.py`: Helper methods (`_find_calendar`, `_find_task`, `_parse_due_date`) prevent code duplication
- `src/core/models.py`: Pydantic models for MCP tool parameters
- `src/providers/base.py`: CalendarProvider protocol defining the interface
- `config.py`: Dynaconf setup and calendar configuration validation

## VCALENDAR Parsing

Custom parser in `src/utils/vcalendar_parser.py` handles:
- Multiline property support (continuation lines starting with whitespace)
- Property extraction from VTODO entries
- Limitations: Basic implementation, handles most common cases