from datetime import date
from caldav import Todo
from pydantic import BaseModel, Field

from ..utils.vcalendar_parser import vcalendar_to_dict


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