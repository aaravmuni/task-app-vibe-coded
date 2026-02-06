# models.py
# Data models for the task tracker.
from dataclasses import dataclass, asdict
from typing import List, Optional
import uuid

@dataclass
class Label:
    id: str
    name: str
    color: str  # hex string like "#ff00aa"

    @staticmethod
    def new(name: str, color: str) -> "Label":
        return Label(id=str(uuid.uuid4()), name=name, color=color)

@dataclass
class Task:
    id: str
    title: str
    progress: int  # 0..100
    label_id: Optional[str]
    column: str  # "todo" | "in_progress" | "done"

    @staticmethod
    def new(title: str, label_id: Optional[str]) -> "Task":
        return Task(id=str(uuid.uuid4()), title=title, progress=0, label_id=label_id, column="todo")
