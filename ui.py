# ui.py
# Main GUI: columns, task widgets, dialogs, main window.

from PyQt5 import QtWidgets, QtCore, QtGui
from models import Task, Label
from typing import List, Dict, Optional, Callable
import styles
import storage

# Column identifiers and human labels
COLUMN_ORDER = [("todo", "TO-DO"), ("in_progress", "IN PROGRESS"), ("done", "COMPLETED")]

class TaskWidget(QtWidgets.QFrame):
    """A visual card representing a Task with title, label chip, progress bar, and left/right move buttons."""
    def __init__(self, task: Task, label_lookup: Dict[str, Label], on_move: Callable[[Task, str], None], on_update: Callable[[Task], None]):
        super().__init__()
        self.setObjectName("card")
        self.task = task
        self.label_lookup = label_lookup
        self.on_move = on_move
        self.on_update = on_update
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8,8,8,8)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)

        title = QtWidgets.QLabel(self.task.title)
        title.setObjectName("title")
        title.setProperty("class", "title")
        title.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        top.addWidget(title)

        top.addStretch()

        # Move left button
        self.btn_left = QtWidgets.QPushButton("◀")
        self.btn_left.setToolTip("Move left")
        self.btn_left.clicked.connect(lambda: self._move("left"))
        top.addWidget(self.btn_left)

        # Move right button
        self.btn_right = QtWidgets.QPushButton("▶")
        self.btn_right.setToolTip("Move right")
        self.btn_right.clicked.connect(lambda: self._move("right"))
        top.addWidget(self.btn_right)

        layout.addLayout(top)

        # Label chip + editable label name
        label_row = QtWidgets.QHBoxLayout()
        label_row.setSpacing(8)
        label = self.label_lookup.get(self.task.label_id, None)
        if label:
            chip = QtWidgets.QLabel(label.name)
            chip.setStyleSheet(f"padding: 4px 8px; border-radius: 8px; background: {label.color}; color: white;")
            label_row.addWidget(chip)
        else:
            chip = QtWidgets.QLabel("No Label")
            chip.setObjectName("muted")
            label_row.addWidget(chip)
        label_row.addStretch()
        layout.addLayout(label_row)

        # Progress bar with slider
        progress_row = QtWidgets.QHBoxLayout()
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setRange(0,100)
        self.progressbar.setValue(self.task.progress)
        self.progressbar.setTextVisible(True)
        self.progressbar.setFormat(f"{self.task.progress}%")
        self.progressbar.setFixedHeight(12)
        progress_row.addWidget(self.progressbar)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setValue(self.task.progress)
        self.slider.setFixedWidth(100)
        self.slider.valueChanged.connect(self._on_progress_change)
        progress_row.addWidget(self.slider)
        layout.addLayout(progress_row)

        # Footer: small controls
        footer = QtWidgets.QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch()
        # Edit title button
        self.btn_edit = QtWidgets.QPushButton("✎")
        self.btn_edit.setToolTip("Edit title")
        self.btn_edit.clicked.connect(self._edit_title)
        footer.addWidget(self.btn_edit)
        # Delete
        self.btn_delete = QtWidgets.QPushButton("🗑")
        self.btn_delete.setToolTip("Delete task")
        footer.addWidget(self.btn_delete)
        layout.addLayout(footer)

        # wire delete (outside caller will re-add callback)
        self.btn_delete.clicked.connect(lambda: self.on_update_delete())

    def _move(self, direction: str):
        """Compute target column and call on_move callback with updated task."""
        current_index = [c[0] for c in COLUMN_ORDER].index(self.task.column)
        if direction == "left" and current_index > 0:
            target = COLUMN_ORDER[current_index-1][0]
            self.task.column = target
            self.on_move(self.task, target)
        elif direction == "right" and current_index < len(COLUMN_ORDER)-1:
            target = COLUMN_ORDER[current_index+1][0]
            self.task.column = target
            self.on_move(self.task, target)
        else:
            # nothing
            pass

    def _on_progress_change(self, val: int):
        self.task.progress = int(val)
        self.progressbar.setValue(val)
        self.progressbar.setFormat(f"{val}%")
        self.on_update(self.task)

    def _edit_title(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Edit task title", "Title:", text=self.task.title)
        if ok and text.strip():
            self.task.title = text.strip()
            # update displayed title
            title_label = self.findChild(QtWidgets.QLabel)
            # simpler: rebuild content or update first label
            for child in self.findChildren(QtWidgets.QLabel):
                if child.property("class") == "title":
                    child.setText(self.task.title)
                    break
            self.on_update(self.task)

    def on_update_delete(self):
        """A placeholder to be replaced by the owning ColumnWidget when the widget is created."""
        # By default do nothing; owner should override attribute to delete task
        pass

class ColumnWidget(QtWidgets.QFrame):
    """A column (TO-DO / IN PROGRESS / DONE) that holds TaskWidgets."""
    def __init__(self, key: str, title: str, label_lookup: Dict[str, Label]):
        super().__init__()
        self.setObjectName("panel")
        self.key = key
        self.title = title
        self.label_lookup = label_lookup
        self.tasks: List[Task] = []
        self.task_widgets: Dict[str, TaskWidget] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel(self.title)
        header.setStyleSheet("font-weight: 700; padding: 4px;")
        layout.addWidget(header)
        layout.addSpacing(6)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.inner = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(self.inner)
        self.inner_layout.setSpacing(10)
        self.inner_layout.addStretch()
        self.scroll.setWidget(self.inner)
        layout.addWidget(self.scroll)

    def set_tasks(self, tasks: List[Task], on_move: Callable[[Task,str], None], on_update: Callable[[Task], None], on_delete: Callable[[Task], None]):
        """Clear & add tasks for this column."""
        # clear existing widgets
        for w in list(self.task_widgets.values()):
            w.setParent(None)
        self.task_widgets.clear()
        # add tasks
        # keep insertion order
        for t in tasks:
            if t.column != self.key:
                continue
            widget = TaskWidget(t, self.label_lookup, on_move, on_update)
            # hook delete handler
            def make_delete_fn(task_obj):
                def _delete():
                    on_delete(task_obj)
                return _delete
            widget.on_update_delete = make_delete_fn(t)
            # store and insert before the stretch
            self.task_widgets[t.id] = widget
            self.inner_layout.insertWidget(self.inner_layout.count()-1, widget)

    def add_task_widget(self, task: Task, on_move, on_update, on_delete):
        task.column = self.key
        self.tasks.append(task)
        widget = TaskWidget(task, self.label_lookup, on_move, on_update)
        widget.on_update_delete = lambda: on_delete(task)
        self.task_widgets[task.id] = widget
        self.inner_layout.insertWidget(self.inner_layout.count()-1, widget)

    def refresh_labels(self, label_lookup: Dict[str, Label]):
        """If label colors/names changed, update chips inside each task widget."""
        self.label_lookup = label_lookup
        for w in self.task_widgets.values():
            # rebuild the label part by simple approach: setParent and rebuild
            w.label_lookup = label_lookup
            # naive: remove and recreate widget text; simplest is to just update first label found
            for child in w.findChildren(QtWidgets.QLabel):
                if child.property("class") == "title":
                    continue
                # update the chip by searching for label id
            # For simplicity, we won't fully reconstruct here. The app triggers full reload on label edits.

class LabelDialog(QtWidgets.QDialog):
    """Dialog to add/edit labels."""
    def __init__(self, labels: List[Label], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Labels")
        self.resize(400, 300)
        self.labels = labels  # list reference; we will modify in-place
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self._reload_list()
        layout.addWidget(self.list_widget)

        form = QtWidgets.QHBoxLayout()
        self.name_in = QtWidgets.QLineEdit()
        self.name_in.setPlaceholderText("Label name")
        self.color_in = QtWidgets.QLineEdit()
        self.color_in.setPlaceholderText("#rrggbb")
        self.pick_color = QtWidgets.QPushButton("Pick")
        self.pick_color.clicked.connect(self._pick_color)
        form.addWidget(self.name_in)
        form.addWidget(self.color_in)
        form.addWidget(self.pick_color)
        layout.addLayout(form)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add")
        self.add_btn.clicked.connect(self._add_label)
        self.edit_btn = QtWidgets.QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self._edit_selected)
        self.delete_btn = QtWidgets.QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.delete_btn)
        layout.addLayout(btns)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _reload_list(self):
        self.list_widget.clear()
        for l in self.labels:
            item = QtWidgets.QListWidgetItem(f"{l.name} ({l.color})")
            item.setData(QtCore.Qt.UserRole, l.id)
            self.list_widget.addItem(item)

    def _pick_color(self):
        col = QtWidgets.QColorDialog.getColor()
        if col.isValid():
            self.color_in.setText(col.name())

    def _add_label(self):
        name = self.name_in.text().strip()
        color = self.color_in.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Invalid", "Label name required.")
            return
        # create new label
        from models import Label as LabelModel
        new_label = LabelModel.new(name, color or "#777777")
        self.labels.append(new_label)
        self.name_in.clear()
        self.color_in.clear()
        self._reload_list()

    def _edit_selected(self):
        sel = self.list_widget.currentItem()
        if not sel:
            return
        lid = sel.data(QtCore.Qt.UserRole)
        lbl = next((x for x in self.labels if x.id == lid), None)
        if not lbl:
            return
        name = self.name_in.text().strip() or lbl.name
        color = self.color_in.text().strip() or lbl.color
        lbl.name = name
        lbl.color = color
        self._reload_list()

    def _delete_selected(self):
        sel = self.list_widget.currentItem()
        if not sel:
            return
        lid = sel.data(QtCore.Qt.UserRole)
        self.labels[:] = [l for l in self.labels if l.id != lid]
        self._reload_list()
