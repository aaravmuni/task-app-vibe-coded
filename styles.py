# styles.py
# Centralized color and style configuration. Modify these to change the look.

# Theme colors (dark by default)
BG = "#0F1115"        # main background
PANEL = "#14161A"     # panel background
CARD = "#181A1E"      # task card background
TEXT = "#E6EEF3"      # primary text
MUTED = "#9AA6B2"     # muted text
ACCENT = "#1BC15B"    # default accent (used when there's no label)
CARD_ELEV = "rgba(124,92,255,0.06)"

# Base font size (pixels) used by scaling function
BASE_FONT_SIZE = 14

def qss(font_size_px: int = BASE_FONT_SIZE) -> str:
    """Return the stylesheet with a given base font size (px)."""
    return f"""
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: "Segoe UI", Roboto, Arial, sans-serif;
        font-size: {font_size_px}px;
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
        font-weight: 700;
        color: {TEXT};
    }}

    QLabel.muted {{
        color: {MUTED};
        font-size: {max(11, font_size_px - 2)}px;
    }}

    QProgressBar {{
        background-color: rgba(255,255,255,0.04);
        border: none;
        height: 12px;
        border-radius: 6px;
        text-align: center;
        font-size: {max(10, font_size_px - 4)}px;
    }}

    QProgressBar::chunk {{
        background: {ACCENT};
        border-radius: 6px;
    }}

    QLineEdit, QComboBox {{
        background-color: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.03);
        padding: 6px;
        border-radius: 6px;
        color: {TEXT};
    }}

    QScrollArea {{
        border: none;
    }}
    """
