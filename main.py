# main.py
# Entry point: builds the main window, loads data, wires save/load and user actions.

import sys
from PyQt5 import QtWidgets, QtCore
import styles
import storage
from ui import ColumnWidget, LabelDialog, COLUMN_ORDER
from models import Task, Label

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Task Tracker")
        self.resize(1000, 640)
        # load data
        self.tasks, self.labels = storage.load_data()
        # map for quick label lookup
        self._rebuild_label_lookup()
        self._build_ui()
        # autosave on close
        self.setStyleSheet(styles.QSS)

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

        toolbar.addWidget(self.add_task_btn)
        toolbar.addWidget(self.manage_labels_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # columns area
        columns_area = QtWidgets.QHBoxLayout()
        self.columns = {}
        for key, title in COLUMN_ORDER:
            col = ColumnWidget(key, title, self.label_lookup)
            self.columns[key] = col
            columns_area.addWidget(col)
        layout.addLayout(columns_area)

        # fill columns with tasks
        self.refresh_columns()

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
        # task already updated by widget; ensure it's in list and save
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        else:
            self.tasks.append(task)
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _on_task_update(self, task: Task):
        # update in list
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        storage.save_data(self.tasks, self.labels)
        # no need to refresh full columns for merely progress change

    def _on_task_delete(self, task: Task):
        self.tasks[:] = [t for t in self.tasks if t.id != task.id]
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _create_task_dialog(self):
        # prompt user for name and label
        title, ok = QtWidgets.QInputDialog.getText(self, "New task", "Task name:")
        if not ok or not title.strip():
            return
        # choose label from existing labels
        items = [l.name for l in self.labels]
        items.insert(0, "No label")
        item, ok2 = QtWidgets.QInputDialog.getItem(self, "Assign label", "Label:", items, 0, False)
        if not ok2:
            return
        label_id = None
        if item and item != "No label":
            selected_label = next((l for l in self.labels if l.name == item), None)
            if selected_label:
                label_id = selected_label.id
        new_task = Task.new(title.strip(), label_id)
        self.tasks.append(new_task)
        storage.save_data(self.tasks, self.labels)
        self.refresh_columns()

    def _open_label_manager(self):
        dlg = LabelDialog(self.labels, parent=self)
        res = dlg.exec_()
        if res:
            # user clicked close (accept)
            pass
        # after dialog close, ensure label lookup updated and tasks saved
        self._rebuild_label_lookup()
        # if label ids changed (delete), ensure tasks referencing deleted labels are cleaned
        valid_ids = {l.id for l in self.labels}
        for t in self.tasks:
            if t.label_id and t.label_id not in valid_ids:
                t.label_id = None
        storage.save_data(self.tasks, self.labels)
        # refresh UI
        self.refresh_columns()

    def closeEvent(self, event):
        # save before closing
        storage.save_data(self.tasks, self.labels)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
