# storage.py
# Handles saving/loading tasks & labels to/from a JSON file.

import json
from typing import Tuple, List
from pathlib import Path
from models import Task, Label
import os

DATA_FILE = Path(os.path.dirname(__file__)) / "tasks.json"

def load_data() -> Tuple[List[Task], List[Label]]:
    if not DATA_FILE.exists():
        # Return default sample labels and empty tasks
        default_labels = [
            Label.new("General", "#4CAF50"),
            Label.new("Bug", "#F44336"),
            Label.new("Feature", "#2196F3"),
        ]
        return [], default_labels
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    tasks = [Task(**t) for t in raw.get("tasks", [])]
    labels = [Label(**l) for l in raw.get("labels", [])]
    return tasks, labels

def save_data(tasks: List[Task], labels: List[Label]) -> None:
    raw = {
        "tasks": [vars(t) for t in tasks],
        "labels": [vars(l) for l in labels],
    }
    DATA_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")
