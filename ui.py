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
        layout.setSpacing(8)
        layout.setContentsMargins(10,10,10,10)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)

        # Title label
        self.title_label = QtWidgets.QLabel(self.task.title)
        self.title_label.setProperty("class", "title")
        self.title_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        top.addWidget(self.title_label)

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

        # Label chip row
        label_row = QtWidgets.QHBoxLayout()
        label_row.setSpacing(8)
        self.chip = QtWidgets.QLabel()
        self.chip.setContentsMargins(4,2,4,2)
        self.chip.setStyleSheet("border-radius: 8px; padding: 4px 8px;")
        label_row.addWidget(self.chip)
        label_row.addStretch()
        layout.addLayout(label_row)

        # Progress row: progressbar + slider
        progress_row = QtWidgets.QHBoxLayout()
        progress_row.setSpacing(8)
        self.progressbar = QtWidgets.QProgressBar()
        self.progressbar.setRange(0,100)
        self.progressbar.setValue(self.task.progress)
        self.progressbar.setTextVisible(True)
        self.progressbar.setFormat(f"{self.task.progress}%")
        self.progressbar.setFixedHeight(16)
        progress_row.addWidget(self.progressbar, 1)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0,100)
        self.slider.setValue(self.task.progress)
        self.slider.setFixedWidth(110)
        self.slider.valueChanged.connect(self._on_progress_change)
        progress_row.addWidget(self.slider)
        layout.addLayout(progress_row)

        # Footer with edit/delete
        footer = QtWidgets.QHBoxLayout()
        footer.addStretch()
        self.btn_edit = QtWidgets.QPushButton("✎")
        self.btn_edit.setToolTip("Edit title")
        self.btn_edit.clicked.connect(self._edit_title)
        footer.addWidget(self.btn_edit)
        self.btn_delete = QtWidgets.QPushButton("🗑")
        self.btn_delete.setToolTip("Delete task")
        footer.addWidget(self.btn_delete)
        layout.addLayout(footer)

        # during build, style the chip and progressbar according to label
        self.refresh_label(self.label_lookup)

        # wire delete (external owner will override this attribute)
        self.btn_delete.clicked.connect(lambda: self.on_update_delete())

    def _move(self, direction: str):
        current_index = [c[0] for c in COLUMN_ORDER].index(self.task.column)
        if direction == "left" and current_index > 0:
            target = COLUMN_ORDER[current_index-1][0]
            self.task.column = target
            self.on_move(self.task, target)
        elif direction == "right" and current_index < len(COLUMN_ORDER)-1:
            target = COLUMN_ORDER[current_index+1][0]
            self.task.column = target
            self.on_move(self.task, target)

    def _on_progress_change(self, val: int):
        self.task.progress = int(val)
        self.progressbar.setValue(val)
        self.progressbar.setFormat(f"{val}%")
        self.on_update(self.task)

    def _edit_title(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Edit task title", "Title:", text=self.task.title)
        if ok and text.strip():
            self.task.title = text.strip()
            self.title_label.setText(self.task.title)
            self.on_update(self.task)

    def refresh_label(self, label_lookup: Dict[str, Label]):
        """Update chip text/color and progressbar color according to the task's label."""
        self.label_lookup = label_lookup
        label = None
        if self.task.label_id:
            label = label_lookup.get(self.task.label_id)
        if label:
            self.chip.setText(label.name)
            # text color: decide white or dark based on color brightness
            text_color = "#ffffff"
            self.chip.setStyleSheet(f"border-radius: 8px; padding: 4px 8px; background: {label.color}; color: {text_color};")
            # style the progressbar chunk to match the label
            self.progressbar.setStyleSheet(
                f"QProgressBar {{ background-color: rgba(255,255,255,0.03); border-radius: 6px; height: 16px; }} "
                f"QProgressBar::chunk {{ background: {label.color}; border-radius: 6px; }}"
            )
            # style the arrow buttons: hover outline using label color
            btn_styles = (
                "QPushButton {{ border-radius:6px; padding:6px; border:1px solid rgba(255,255,255,0.02); }} "
                f"QPushButton:hover {{ outline: 2px solid {label.color}; background-color: rgba(255,255,255,0.02); }}"
            )
            self.btn_left.setStyleSheet(btn_styles)
            self.btn_right.setStyleSheet(btn_styles)
        else:
            # no label - muted chip
            self.chip.setText("No Label")
            self.chip.setStyleSheet("border-radius: 8px; padding: 4px 8px; background: rgba(255,255,255,0.02); color: #cfd8dc;")
            # default progress chunk
            self.progressbar.setStyleSheet("")
            # reset button style
            base = "QPushButton {{ border-radius:6px; padding:6px; border:1px solid rgba(255,255,255,0.02); }} QPushButton:hover {{ background-color: rgba(255,255,255,0.02); }}"
            self.btn_left.setStyleSheet(base)
            self.btn_right.setStyleSheet(base)

    def on_update_delete(self):
        """A placeholder to be replaced by the owning ColumnWidget when the widget is created."""
        pass


class ColumnWidget(QtWidgets.QFrame):
    """A column (TO-DO / IN PROGRESS / DONE) that holds TaskWidgets."""
    def __init__(self, key: str, title: str, label_lookup: Dict[str, Label]):
        super().__init__()
        self.setObjectName("panel")
        self.key = key
        self.title = title
        self.label_lookup = label_lookup
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
        # add tasks in order
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
            self.task_widgets[t.id] = widget
            self.inner_layout.insertWidget(self.inner_layout.count()-1, widget)

    def refresh_labels(self, label_lookup: Dict[str, Label]):
        """If label colors/names changed, update chips inside each task widget."""
        self.label_lookup = label_lookup
        for w in self.task_widgets.values():
            w.refresh_label(label_lookup)


class LabelDialog(QtWidgets.QDialog):
    """Dialog to add/edit labels. Emits labelsChanged when any modification occurs."""
    labelsChanged = QtCore.pyqtSignal()

    def __init__(self, labels: List[Label], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Labels")
        self.resize(500, 360)
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
        from models import Label as LabelModel
        new_label = LabelModel.new(name, color or "#777777")
        self.labels.append(new_label)
        self.name_in.clear()
        self.color_in.clear()
        self._reload_list()
        # inform listeners
        self.labelsChanged.emit()

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
        self.labelsChanged.emit()

    def _delete_selected(self):
        sel = self.list_widget.currentItem()
        if not sel:
            return
        lid = sel.data(QtCore.Qt.UserRole)
        self.labels[:] = [l for l in self.labels if l.id != lid]
        self._reload_list()
        self.labelsChanged.emit()


class LabelPickDialog(QtWidgets.QDialog):
    """Simple dialog to pick a label; returns label.id or None for 'No label'."""
    def __init__(self, labels: List[Label], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pick label")
        self.resize(360, 120)
        self.labels = labels
        self.selected_id: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItem("No label", userData=None)
        for l in self.labels:
            self.combo.addItem(l.name, userData=l.id)
        layout.addWidget(self.combo)

        btns = QtWidgets.QHBoxLayout()
        ok = QtWidgets.QPushButton("OK")
        ok.clicked.connect(self._ok)
        cancel = QtWidgets.QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(ok)
        btns.addWidget(cancel)
        layout.addLayout(btns)

    def _ok(self):
        self.selected_id = self.combo.currentData()
        self.accept()
