# main.py
# Entry point: builds the main window, loads data, wires save/load and user actions.

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import styles
import storage
from ui import ColumnWidget, LabelDialog, LabelPickDialog, COLUMN_ORDER
from models import Task, Label

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app: QtWidgets.QApplication):
        super().__init__()
        self.app = app
        self.setWindowTitle("Minimal Task Tracker")
        # start with a larger default window
        self.resize(1200, 760)

        # scale (multiplier) applied to stylesheet font-size
        self.scale = 1.0
        self.base_font = styles.BASE_FONT_SIZE

        # load data
        self.tasks, self.labels = storage.load_data()
        self._rebuild_label_lookup()
        self._build_ui()
        # apply initial qss
        self.apply_stylesheet()

    def _rebuild_label_lookup(self):
        self.label_lookup = {l.id: l for l in self.labels}

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        toolbar = QtWidgets.QHBoxLayout()

        self.add_task_btn = QtWidgets.QPushButton("＋ New Task")
        self.add_task_btn.clicked.connect(self._create_task_dialog)
        self.manage_labels_btn = QtWidgets.QPushButton("Labels")
        self.manage_labels_btn.clicked.connect(self._open_label_manager)

        # scale controls
        self.btn_scale_down = QtWidgets.QPushButton("A−")
        self.btn_scale_down.setToolTip("Decrease UI size")
        self.btn_scale_down.clicked.connect(lambda: self._change_scale(-0.1))
        self.btn_scale_up = QtWidgets.QPushButton("A＋")
        self.btn_scale_up.setToolTip("Increase UI size")
        self.btn_scale_up.clicked.connect(lambda: self._change_scale(+0.1))

        toolbar.addWidget(self.add_task_btn)
        toolbar.addWidget(self.manage_labels_btn)
        toolbar.addWidget(self.btn_scale_down)
        toolbar.addWidget(self.btn_scale_up)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # columns area
        columns_area = QtWidgets.QHBoxLayout()
        self.columns = {}
        for key, title in COLUMN_ORDER:
            col = ColumnWidget(key, title, self.label_lookup)
            self.columns[key] = col
            columns_area.addWidget(col, 1)
        layout.addLayout(columns_area)

        # fill columns with tasks
        self.refresh_columns()

    def apply_stylesheet(self):
        font_px = max(10, int(self.base_font * self.scale))
        self.app.setStyleSheet(styles.qss(font_size_px=font_px))
        # also adjust global application font (helps some controls)
        f = QtGui.QFont()
        f.setPointSize(max(9, int(font_px * 0.9)))
        self.app.setFont(f)

    def _change_scale(self, delta: float):
        self.scale = max(0.7, min(1.6, self.scale + delta))
        self.apply_stylesheet()
        # After scaling we may want to force relayout/resize
        self.adjustSize()

    def refresh_columns(self):
        # update label lookup (maybe changed)
        self._rebuild_label_lookup()
        tasks_by_col = {k: [] for k,_ in COLUMN_ORDER}
        for t in self.tasks:
            tasks_by_col.setdefault(t.column, []).append(t)
        for key, _ in COLUMN_ORDER:
            col_widget = self.columns[key]
            col_widget.set_tasks(tasks_by_col.get(key, []), self._on_task_move, self._on_task_update, self._on_task_delete)

    def _on_task_move(self, task: Task, target_col: str):
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        else:
            self.tasks.append(task)
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _on_task_update(self, task: Task):
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        storage.save_data(self.tasks, self.labels)

    def _on_task_delete(self, task: Task):
        self.tasks[:] = [t for t in self.tasks if t.id != task.id]
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _create_task_dialog(self):
        title, ok = QtWidgets.QInputDialog.getText(self, "New task", "Task name:")
        if not ok or not title.strip():
            return
        # Use the LabelPickDialog which returns the label id directly (avoids name collisions)
        pick = LabelPickDialog(self.labels, parent=self)
        if pick.exec_() != QtWidgets.QDialog.Accepted:
            return
        label_id = pick.selected_id  # may be None for "No label"
        new_task = Task.new(title.strip(), label_id)
        self.tasks.append(new_task)
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _open_label_manager(self):
        dlg = LabelDialog(self.labels, parent=self)
        # listen to signals so we update immediately if labels are changed
        dlg.labelsChanged.connect(self._on_labels_changed)
        dlg.exec_()
        # After closed ensure label sync just in case
        self._on_labels_changed()

    def _on_labels_changed(self):
        # Rebuild label lookup & sanitize tasks referencing deleted labels
        self._rebuild_label_lookup()
        valid_ids = {l.id for l in self.labels}
        for t in self.tasks:
            if t.label_id and t.label_id not in valid_ids:
                t.label_id = None
        storage.save_data(self.tasks, self.labels)
        # Refresh columns and widgets to pick up new colors/names
        for col in self.columns.values():
            col.refresh_labels(self.label_lookup)
        # If tasks were changed (label deleted) also refresh the whole layout
        self.refresh_columns()

    def closeEvent(self, event):
        storage.save_data(self.tasks, self.labels)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())
