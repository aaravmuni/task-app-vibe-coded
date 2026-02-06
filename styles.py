# styles.py
# Centralized color and style configuration. Modify these to change the look.

# Theme colors (dark by default)
BG = "#0F1115"        # main background
PANEL = "#14161A"     # panel background
CARD = "#181A1E"      # task card background
TEXT = "#E6EEF3"      # primary text
MUTED = "#9AA6B2"     # muted text
ACCENT = "#7C5CFF"    # accent color
CARD_ELEV = "rgba(124,92,255,0.06)"

# Very simple stylesheet for PyQt widgets.
QSS = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 12px;
}}

QFrame#panel {{
    background-color: {PANEL};
    border-radius: 10px;
}}

QFrame#card {{
    background-color: {CARD};
    border-radius: 10px;
    padding: 8px;
}}

QPushButton {{
    background: transparent;
    border: none;
    padding: 6px;
}}

QPushButton:hover {{
    background-color: rgba(255,255,255,0.03);
    border-radius: 6px;
}}

QLabel.title {{
    font-weight: 600;
    color: {TEXT};
}}

QLabel.muted {{
    color: {MUTED};
    font-size: 11px;
}}

QProgressBar {{
    background-color: rgba(255,255,255,0.04);
    border: none;
    height: 10px;
    border-radius: 5px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 #a98cff);
    border-radius: 5px;
}}

QLineEdit, QComboBox {{
    background-color: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.03);
    padding: 6px;
    border-radius: 6px;
    color: {TEXT};
}}
"""
