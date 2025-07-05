from datetime import date
from caldav import Todo
from pydantic import BaseModel, Field


def vcalendar_to_dict(vcal_data: str) -> dict:
    """Parse VCALENDAR data into a dictionary.

    Note: This simple implementation has limitations:
    - Properties with colons in values will be split incorrectly
    - VTODO-specific properties only, ignores VCALENDAR wrapper
    """
    result = {}
    lines = vcal_data.strip().split("\n")
    current_key = None

    for line in lines:
        stripped_line = line.strip()

        # Skip BEGIN/END lines
        if stripped_line.startswith(("BEGIN:", "END:")):
            continue

        # Check if it's a continuation line (starts with whitespace)
        if line.startswith((" ", "\t")) and current_key:
            result[current_key] += "\n" + stripped_line
        elif ":" in stripped_line:
            key, value = stripped_line.split(":", 1)
            result[key] = value
            current_key = key

    return result


class Task(BaseModel):
    name: str
    due_on: date | None
    completed: bool
    status: str | None = Field(default=None)

    @classmethod
    def from_todo(cls, todo: Todo):
        props = vcalendar_to_dict(todo.data)

        return cls(
            name=props.get("SUMMARY", "Untitled Task"),
            due_on=todo.get_due(),
            completed=props.get("STATUS") == "COMPLETED",
            status=props.get("STATUS"),
        )
