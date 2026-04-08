# Financial group project dashboard

import sys
import sqlite3
import calendar
from datetime import datetime
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QStackedWidget,
    QFrame, QMessageBox, QSizePolicy, QHeaderView, QInputDialog, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QAction, QPixmap, QPainter, QPainterPath, QLinearGradient, QColor, QPen
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from finance_logic import get_monthly_breakdown, get_yearly_category_series


DB_NAME = "finance.db"


class DoubleClickableLabel(QLabel):
    """A QLabel that opens a dialog on double-click to edit its text."""

    def __init__(self, text: str, on_change=None, parent: QWidget | None = None):
        super().__init__(text, parent)
        self._on_change = on_change
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to edit")

    def mouseDoubleClickEvent(self, event): 
        current = self.text()
        new_text, ok = QInputDialog.getText(
            self,
            "Edit",
            "Enter value:",
            QLineEdit.EchoMode.Normal,
            current,
        )
        if ok:
            new_text = (new_text or "").strip()
            if new_text:
                self.setText(new_text)
                if callable(self._on_change):
                    self._on_change(new_text)


class ProfileCircle(QFrame):
    """A profile circle widget that can update its background via image selection."""

    def __init__(self, on_change=None, parent: QWidget | None = None):
        super().__init__(parent)
        self._on_change = on_change
        self.setFixedSize(72, 72)
        self.setObjectName("profile_circle")
        self._pixmap = None
        self._image_path = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to choose profile picture")

    def _set_image_style(self, image_path: str):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._image_path = image_path
        self.update()
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        clip_path = QPainterPath()
        clip_path.addEllipse(rect)
        painter.setClipPath(clip_path)

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, QColor("#4facfe"))
            gradient.setColorAt(1.0, QColor("#00f2fe"))
            painter.fillPath(clip_path, gradient)

        painter.setClipping(False)
        border_pen = QPen(QColor(255, 255, 255, 20), 2)
        painter.setPen(border_pen)
        painter.drawEllipse(rect)

    def mouseDoubleClickEvent(self, event):  #
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Profile Picture",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)",
        )
        if not file_path:
            return
        if self._set_image_style(file_path) and callable(self._on_change):
            self._on_change(file_path)

class CreditCardWidget(QFrame):
    """Improved Credit Card Widget - now fits perfectly (no more cramped/scaled text)"""
    def __init__(self, full_card_number: str = "", on_change=None, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        self._full_card = (full_card_number or "0000000000000000").replace(" ", "")
        self._revealed = False

        self.setObjectName("card")
        self.setFixedHeight(138)                    
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to reveal full number\nDouble-click to edit")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)   
        layout.setSpacing(6)

        # Title
        self.title = QLabel("Card")
        self.title.setObjectName("card_title")
        self.title.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.title)

        # Card Number
        self.number_label = DoubleClickableLabel(
            self.get_masked(), on_change=self._on_card_edit
        )
        self.number_label.setObjectName("card_value")
        self.number_label.setStyleSheet("""
            font-size: 17.5px; 
            font-family: monospace; 
            letter-spacing: 3.5px;
        """)
        layout.addWidget(self.number_label)

        # Balance
        self.balance_label = QLabel("$0.00")
        self.balance_label.setObjectName("card_value")
        self.balance_label.setStyleSheet("""
            font-size: 21px; 
            font-weight: bold; 
            color: #4ade80;
        """)
        layout.addWidget(self.balance_label)

    def get_masked(self):
        if self._revealed and len(self._full_card) >= 4:
            c = self._full_card.ljust(16, "X")[:16]
            return " ".join([c[i:i+4] for i in range(0, 16, 4)])
        else:
            last4 = self._full_card[-4:] if len(self._full_card) >= 4 else self._full_card
            return f"•••• •••• •••• {last4}"

    def update_display(self):
        self.number_label.setText(self.get_masked())

    def mousePressEvent(self, event): 
        self._revealed = True
        self.update_display()
        QTimer.singleShot(6000, self._hide_reveal)
        super().mousePressEvent(event)

    def _hide_reveal(self):
        self._revealed = False
        self.update_display()

    def _on_card_edit(self, new_text):
        cleaned = "".join(c for c in (new_text or "") if c.isdigit())
        if len(cleaned) >= 13:
            self._full_card = cleaned
            self.update_display()
            if callable(self._on_change):
                self._on_change(cleaned)

    def update_balance(self, balance: float):
        self.balance_label.setText(f"${balance:,.2f}")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        target REAL,
        progress REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        value REAL,
        date TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        status TEXT
    )""")
    
  
    c.execute("""
    CREATE TABLE IF NOT EXISTS profile_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL DEFAULT 'User Name',
        role TEXT NOT NULL DEFAULT 'Role',
        image_path TEXT,
        card_number TEXT DEFAULT '0000000000000000'
    )""")


    try:
        c.execute("ALTER TABLE profile_settings ADD COLUMN card_number TEXT DEFAULT '0000000000000000'")
    except sqlite3.OperationalError:
        pass  

    c.execute("""
    INSERT OR IGNORE INTO profile_settings (id, name, role, image_path, card_number)
    VALUES (1, 'User Name', 'Role', NULL, '0000000000000000')
    """)
    conn.commit()
    conn.close()


def get_profile_settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, role, image_path, card_number FROM profile_settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if not row:
        return {"name": "User Name", "role": "Role", "image_path": None, "card_number": "0000000000000000"}
    return {
        "name": row[0] or "User Name",
        "role": row[1] or "Role",
        "image_path": row[2],
        "card_number": row[3] or "0000000000000000"
    }

def save_profile_settings(name=None, role=None, image_path=None, card_number=None):
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if role is not None:
        updates.append("role = ?")
        params.append(role)
    if image_path is not None:
        updates.append("image_path = ?")
        params.append(image_path)
    if card_number is not None:
        updates.append("card_number = ?")
        params.append(card_number)
    if not updates:
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        f"UPDATE profile_settings SET {', '.join(updates)} WHERE id = 1",
        tuple(params),
    )
    conn.commit()
    conn.close()

def fetch_month_data(table, year, month):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    month_str = f"{year}-{month:02d}"
    if table in ("income", "expenses"):
        c.execute(
            f"SELECT id, {'source' if table=='income' else 'category'}, amount, date "
            f"FROM {table} WHERE date LIKE ? ORDER BY date, id",
            (month_str + "%",),
        )
    elif table in ("investments", "debts"):
        c.execute(
            f"SELECT id, type, amount, date FROM {table} WHERE date LIKE ? ORDER BY date, id",
            (month_str + "%",),
        )
    elif table == "goals":
        c.execute(
            "SELECT id, name, target, progress, date FROM goals WHERE date LIKE ? ORDER BY date, id",
            (month_str + "%",),
        )
    else:
        rows = []
        conn.close()
        return rows
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_summary(year, month):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    month_str = f"{year}-{month:02d}"
    c.execute("SELECT SUM(amount) FROM income WHERE date LIKE ?", (month_str + "%",))
    income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (month_str + "%",))
    expenses = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM investments WHERE date LIKE ?", (month_str + "%",))
    investments = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM debts WHERE date LIKE ?", (month_str + "%",))
    debts = c.fetchone()[0] or 0
    c.execute("SELECT SUM(value) FROM assets")
    assets = c.fetchone()[0] or 0
    c.execute("SELECT message FROM notifications WHERE status='active'")
    notifications = [r[0] for r in c.fetchall()]
    conn.close()
    return {"income": income, "expenses": expenses, "investments": investments, "debts": debts, "assets": assets, "notifications": notifications}

def save_row(table, row_id, col_values):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    def _upsert(query_insert, query_update, values_insert, values_update):
        if row_id is None:
            c.execute(query_insert, values_insert)
            return
        c.execute(query_update, values_update)
        if c.rowcount == 0:
            c.execute(query_insert, values_insert)

    if table == "income":
        _upsert(
            "INSERT INTO income (source, amount, date) VALUES (?, ?, ?)",
            "UPDATE income SET source=?, amount=?, date=? WHERE id=?",
            (col_values[0], col_values[1], col_values[2]),
            (col_values[0], col_values[1], col_values[2], row_id),
        )
    elif table == "expenses":
        _upsert(
            "INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)",
            "UPDATE expenses SET category=?, amount=?, date=? WHERE id=?",
            (col_values[0], col_values[1], col_values[2]),
            (col_values[0], col_values[1], col_values[2], row_id),
        )
    elif table == "investments":
        if row_id is None:
            c.execute("INSERT INTO investments (type, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE investments SET type=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "debts":
        if row_id is None:
            c.execute("INSERT INTO debts (type, amount, date) VALUES (?, ?, ?)", (col_values[0], col_values[1], col_values[2]))
        else:
            c.execute("UPDATE debts SET type=?, amount=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], row_id))
    elif table == "goals":
        if row_id is None:
            c.execute("INSERT INTO goals (name, target, progress, date) VALUES (?, ?, ?, ?)", (col_values[0], col_values[1], col_values[2], col_values[3]))
        else:
            c.execute("UPDATE goals SET name=?, target=?, progress=?, date=? WHERE id=?", (col_values[0], col_values[1], col_values[2], col_values[3], row_id))
    conn.commit()
    conn.close()


class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=3, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        fig.tight_layout()

    def plot_monthly_category_series(self, labels, values, category, month_name=None):
        self.ax.clear()
        if not labels:
            self.ax.text(0.5, 0.5, "No data", ha="center")
            self.draw()
            return
        line_color = "#4CAF50"
        if category in ("Expenses", "Debts"):
            line_color = "#F44336"
        elif category in ("Investments", "Financial Goals"):
            line_color = "#1E88E5"
        elif category == "Budgeting":
            line_color = "#9C27B0"
        if category == "Budgeting":
            # Graph style
            x = np.arange(len(labels), dtype=float)
            y = np.array(values, dtype=float)
            if len(labels) >= 4:
                xs = np.linspace(x.min(), x.max(), len(labels) * 24)
                ys = np.interp(xs, x, y)
            else:
                xs, ys = x, y

            self.ax.set_facecolor("#121c3a")
            self.ax.fill_between(xs, ys, 0, color="#7d2cff", alpha=0.13)
            self.ax.fill_between(xs, ys, 0, color="#ff2da0", alpha=0.08)
            self.ax.fill_between(xs, ys, 0, color="#5b34ff", alpha=0.10)
            self.ax.plot(xs, ys, color="#c13cff", linewidth=2.5)
            self.ax.scatter(x, y, s=24, color="#ffd0ff", edgecolor="#c13cff", zorder=3)
            self.ax.grid(color="#253056", alpha=0.45, linewidth=0.8)
            self.ax.set_xticks(x, labels)
            self.ax.tick_params(axis="x", colors="#000000", rotation=0)
            self.ax.tick_params(axis="y", colors="#000000")
            self.ax.set_ylabel("Cashflow", color="#000000")
            title_month = month_name or "Current Month"
            self.ax.set_title(f"My CashFlow for {title_month}", color="#000000", fontsize=14, weight="bold")
            for spine in self.ax.spines.values():
                spine.set_color("#26335e")
        else:
            self.ax.plot(labels, values, marker="o", color=line_color, linewidth=2)
            self.ax.set_ylabel("Amount")
            self.ax.set_title(f"{category} Trend (Jan-Dec)")
            self.ax.tick_params(axis="x", rotation=35)
        self.draw()

    def _build_palette(self, count):
        if count <= 0:
            return []
        cmap = plt.cm.hsv
        return [cmap(i / max(1, count)) for i in range(count)]

    def plot_pie_breakdown(self, labels, vals, category):
        self.ax.clear()
        if not vals or sum(vals) == 0:
            self.ax.text(0.5, 0.5, "No data", ha="center")
            self._last_colors = []
        else:
            colors = self._build_palette(len(labels))
            self._last_colors = colors
            self.ax.pie(
                vals,
                labels=None,
                startangle=90,
                colors=colors,
                radius=0.84,
                wedgeprops={"width": 0.22, "edgecolor": "#0f1720"},
            )
            total = sum(vals)
            self.ax.text(0, 0.09, "Budget Report" if category == "Budgeting" else category,
                         ha="center", va="center", color="#000000", fontsize=7, weight="medium")
            self.ax.text(0, -0.05, f"${total:,.2f}",
                         ha="center", va="center", color="#000000", fontsize=7, weight="medium")
            self.ax.text(0, -0.17, "Current Month",
                         ha="center", va="center", color="#000000", fontsize=6, weight= "medium" )
        pie_title = "My Monthly Spendings" if category == "Budgeting" else f"{category} Spending"
        self.ax.set_title(pie_title, color="#000000", y=0.94, pad=1, weight= "bold")
        self.ax.set_aspect("equal")
        self.draw()

    def get_last_colors(self):
        return getattr(self, "_last_colors", [])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Finance Tracker")
        self.setGeometry(80, 40, 1400, 900)
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.current_nav = "Dashboard"
        self.fullscreen = False
        self.profile_settings = get_profile_settings()

        central = QWidget()
        main_layout = QHBoxLayout(central)
        self.setCentralWidget(central)

     
        nav_frame = QFrame()
        nav_frame.setObjectName("nav")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(16, 16, 16, 16)
        nav_layout.setSpacing(12)

        # Profile pic 
        profile_container = QVBoxLayout()
        profile_container.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.profile_circle = ProfileCircle(on_change=self.on_profile_image_changed)
        profile_container.addWidget(
            self.profile_circle, alignment=Qt.AlignmentFlag.AlignHCenter
        )

        # Name and occupation  
        self.name_label = DoubleClickableLabel(
            self.profile_settings["name"],
            on_change=self.on_profile_name_changed,
        )
        self.name_label.setObjectName("sidebar_name")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.role_label = DoubleClickableLabel(
            self.profile_settings["role"],
            on_change=self.on_profile_role_changed,
        )
        self.role_label.setObjectName("sidebar_role")
        self.role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_container.addWidget(self.name_label)
        profile_container.addWidget(self.role_label)
        if self.profile_settings["image_path"]:
            self.profile_circle._set_image_style(self.profile_settings["image_path"])

        nav_layout.addLayout(profile_container)

        # Navigation items
        self.nav_buttons = {}
        nav_items = ["Dashboard", "Budgeting", "Income", "Expenses", "Investments", "Debts", "Financial Goals"]
        for name in nav_items:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(self.make_nav_handler(name))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            nav_layout.addWidget(btn)
            self.nav_buttons[name] = btn

        nav_layout.addStretch()
        main_layout.addWidget(nav_frame, 1)

    
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        # Months
        months_bar = QHBoxLayout()
        months_bar.setSpacing(6)
        self.month_buttons = {}
        for i, m in enumerate(calendar.month_abbr):
            if i == 0: continue
            b = QPushButton(m)
            b.setCheckable(True)
            b.clicked.connect(self.make_month_handler(i))
            months_bar.addWidget(b)
            self.month_buttons[i] = b
        right_layout.addLayout(months_bar)

    
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        self.prev_year_btn = QPushButton("<<")
        self.prev_year_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_year_btn.clicked.connect(lambda: self.change_year(-1))
        header_layout.addWidget(self.prev_year_btn)
        self.date_label = QLabel("")
        header_layout.addWidget(self.date_label)
        self.next_year_btn = QPushButton(">>")
        self.next_year_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_year_btn.clicked.connect(lambda: self.change_year(1))
        header_layout.addWidget(self.next_year_btn)
        right_layout.addLayout(header_layout)

        #  Pages 
        self.stack = QStackedWidget()
        self.pages = {}
        self.pages["Dashboard"] = self.build_dashboard_page()
        self.pages["Budgeting"] = self.build_budgeting_page()
        self.pages["Income"] = self.build_income_page()
        self.pages["Expenses"] = self.build_expenses_page()
        self.pages["Investments"] = self.build_investments_page()
        self.pages["Debts"] = self.build_debts_page()
        self.pages["Financial Goals"] = self.build_goals_page()


        for name, widget in self.pages.items():
            self.stack.addWidget(widget)

        right_layout.addWidget(self.stack, 1)
        main_layout.addWidget(right_frame, 4)

        # Menu 
        toggle_full = QAction("Toggle Fullscreen", self)
        toggle_full.setShortcut("F11")
        toggle_full.triggered.connect(self.toggle_fullscreen)
        self.addAction(toggle_full)

        exit_full = QAction("Exit", self)
        exit_full.setShortcut("Esc")
        exit_full.triggered.connect(self.close)
        self.addAction(exit_full)

        # Styling
        self.setStyleSheet(self.stylesheet())

        # Initialise ui state
        self.select_month(self.current_month)
        self.select_nav("Dashboard")

    def _parse_amount(self, raw_text):
        cleaned = (raw_text or "").strip().replace("$", "").replace(",", "")
        if cleaned == "":
            return 0.0
        return float(cleaned)

    def _normalize_date(self, raw_date):
        text = (raw_date or "").strip()
        if not text:
            return f"{self.current_year}-{self.current_month:02d}-01"
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be YYYY-MM-DD")
        return parsed.strftime("%Y-%m-%d")

    def _commit_table_edits(self, table_widget):
        # Ensure active in cell editor value is committed before reading
        table_widget.clearFocus()
        QApplication.processEvents()

    def _to_hex(self, rgba_color):
        r, g, b = [int(max(0, min(1, c)) * 255) for c in rgba_color[:3]]
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_color_ranking(self, category, labels, values, colors):
        if not labels or not values:
            return f"No {category.lower()} data"
        pairs = list(zip(labels, values, colors))
        pairs.sort(key=lambda item: -float(item[1]))
        top = pairs[:5]
        lines = []
        for label, amount, color in top:
            hex_color = self._to_hex(color)
            lines.append(
                f"<span style='color:{hex_color};'>●</span> "
                f"<b>{label}</b><br>&nbsp;&nbsp;${amount:,.2f}"
            )
        return f"<b>{category} Categories</b><br>" + "<br>".join(lines)

    def queue_save_income_table(self):
        # Let the active editor commit before reading cell values
        QTimer.singleShot(0, self.save_income_table)

    def queue_save_exp_table(self):
        # Let the active editor commit before reading cell values
        QTimer.singleShot(0, self.save_exp_table)


    def build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        cards = QHBoxLayout()
        self.card_balance = self.make_card("Available Balance", "$0")
        self.card_net = self.make_card("Total Net Worth", "$0")
        self.card_income = self.make_card("Income (month)", "$0")
        self.card_expenses = self.make_card("Expenses (month)", "$0")
        cards.addWidget(self.card_balance)
        cards.addWidget(self.card_net)
        cards.addWidget(self.card_income)
        cards.addWidget(self.card_expenses)
        layout.addLayout(cards)

        # Middle:: left charts, right donut + ranking + credit card
        mid = QHBoxLayout()

        # Left: line chart
        left_col = QVBoxLayout()
        self.line_chart = ChartCanvas(width=6, height=3)
        left_col.addWidget(self.line_chart)
        mid.addLayout(left_col, 3)

        # Right: donut + ranking + credit card
        right_col = QVBoxLayout()
        self.pie_chart = ChartCanvas(width=4, height=3)
        right_col.addWidget(self.pie_chart)

        self.ranking_label = QLabel("Income Ranking")
        self.ranking_label.setObjectName("ranking")
        right_col.addWidget(self.ranking_label)

        self.credit_card = CreditCardWidget(
            full_card_number=self.profile_settings.get("card_number", ""),
            on_change=self.on_card_number_changed
        )
        right_col.addWidget(self.credit_card)

        mid.addLayout(right_col, 2)
        layout.addLayout(mid)

        # Bottom: notifications
        self.notif_label = QLabel("")
        self.notif_label.setObjectName("notif")
        layout.addWidget(self.notif_label)

        return page

    def build_budgeting_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Budgeting (editable)"))

        self.butt_table = QTableWidget()
        self.butt_table.setColumnCount(4)
        self.butt_table.setHorizontalHeaderLabels(["ID", "Type", "Amount", "Date (YYYY-MM-DD)"])
        self.butt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.butt_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_budget_row)
        delete_btn.clicked.connect(self.delete_budget_row)
        save_btn.clicked.connect(self.save_butt_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_income_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Income Sources (editable)"))

        self.income_table = QTableWidget()
        self.income_table.setColumnCount(4)
        self.income_table.setHorizontalHeaderLabels(["ID", "Source", "Amount", "Date (YYYY-MM-DD)"])
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.income_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_income_row)
        delete_btn.clicked.connect(self.delete_income_row)
        save_btn.clicked.connect(self.queue_save_income_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_expenses_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Expenses (editable)"))

        self.exp_table = QTableWidget()
        self.exp_table.setColumnCount(4)
        self.exp_table.setHorizontalHeaderLabels(["ID", "Category", "Amount", "Date (YYYY-MM-DD)"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.exp_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_expense_row)
        delete_btn.clicked.connect(self.delete_expense_row)
        save_btn.clicked.connect(self.queue_save_exp_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_investments_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Investments (editable)"))

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(4)
        self.inv_table.setHorizontalHeaderLabels(["ID", "Type", "Amount", "Date (YYYY-MM-DD)"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.inv_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_invest_row)
        delete_btn.clicked.connect(self.delete_invest_row)
        save_btn.clicked.connect(self.save_inv_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_debts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Debts (editable)"))

        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(4)
        self.debt_table.setHorizontalHeaderLabels(["ID", "Type", "Amount", "Date (YYYY-MM-DD)"])
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.debt_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_debt_row)
        delete_btn.clicked.connect(self.delete_debt_row)
        save_btn.clicked.connect(self.save_debt_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_goals_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Financial Goals (editable)"))

        self.goals_table = QTableWidget()
        self.goals_table.setColumnCount(5)
        self.goals_table.setHorizontalHeaderLabels(["ID", "Name", "Target", "Progress", "Date (YYYY-MM-DD)"])
        self.goals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.goals_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("Add Goal")
        delete_btn = QPushButton("Delete Row")
        save_btn = QPushButton("Save Changes")
        add_btn.clicked.connect(self.add_goal_row)
        delete_btn.clicked.connect(self.delete_goal_row)
        save_btn.clicked.connect(self.save_goals_table)
        btns.addWidget(add_btn)
        btns.addWidget(delete_btn)
        btns.addWidget(save_btn)
        layout.addLayout(btns)
        return page

    def build_simple_page(self, title):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size:18px; font-weight:bold;")
        l.addWidget(lbl)
        return w


    def make_card(self, title, value):
        f = QFrame()
        f.setObjectName("card")
        v = QVBoxLayout(f)
        t = QLabel(title)
        t.setObjectName("card_title")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("card_value")
        v.addWidget(t)
        v.addWidget(v_lbl)
        return f

    def make_nav_handler(self, name):
        def handler():
            self.select_nav(name)
        return handler

    def make_month_handler(self, month_index):
        def handler():
            self.select_month(month_index)
        return handler

    def on_profile_name_changed(self, value):
        save_profile_settings(name=value)

    

    def on_profile_role_changed(self, value):
        save_profile_settings(role=value)

    def on_profile_image_changed(self, image_path):
        save_profile_settings(image_path=image_path)

    def on_card_number_changed(self, number):
        save_profile_settings(card_number=number)
        self.profile_settings["card_number"] = number

    def select_nav(self, name):
        self.current_nav = name
        idx = list(self.pages.keys()).index(name)
        self.stack.setCurrentIndex(idx)
        for n, btn in self.nav_buttons.items():
            btn.setStyleSheet(self.nav_button_style(n == name))
        self.refresh_current_page()

    def select_month(self, month_index):
        for i, b in self.month_buttons.items():
            b.setChecked(i == month_index)
            b.setStyleSheet(self.month_button_style(i == month_index))
        self.current_month = month_index
        self.date_label.setText(f"{calendar.month_name[month_index]} {self.current_year}")
        self.refresh_current_page()

    def change_year(self, delta):
        self.current_year += delta
        self.date_label.setText(f"{calendar.month_name[self.current_month]} {self.current_year}")
        self.refresh_current_page()

    def refresh_current_page(self):
        summary = fetch_summary(self.current_year, self.current_month)
        balance = summary["income"] - summary["expenses"]
        net = summary["assets"] + summary["investments"] - summary["debts"] + balance

        self.card_balance.findChild(QLabel, "card_value").setText(f"${balance:,.2f}")
        self.card_net.findChild(QLabel, "card_value").setText(f"${net:,.2f}")
        self.card_income.findChild(QLabel, "card_value").setText(f"${summary['income']:,.2f}")
        self.card_expenses.findChild(QLabel, "card_value").setText(f"${summary['expenses']:,.2f}")
        self.credit_card.update_balance(balance)
        self.credit_card.update_display()
        # noti
        self.notif_label.setText("\n".join(summary["notifications"]) if summary["notifications"] else "")
        # charts
        chart_category = self.current_nav if self.current_nav in (
            "Budgeting", "Income", "Expenses", "Investments", "Debts", "Financial Goals"
        ) else "Budgeting"
        yearly = get_yearly_category_series(chart_category, self.current_year)
        breakdown = get_monthly_breakdown(chart_category, self.current_year, self.current_month)
        self.line_chart.plot_monthly_category_series(
            yearly["labels"],
            yearly["values"],
            chart_category,
            calendar.month_name[self.current_month],
        )
        self.pie_chart.plot_pie_breakdown(breakdown["labels"], breakdown["values"], chart_category)
        colors = self.pie_chart.get_last_colors()
        self.ranking_label.setText(
            self._build_color_ranking(chart_category, breakdown["labels"], breakdown["values"], colors)
        )

    
        current_widget = self.stack.currentWidget()
        if current_widget == self.pages["Income"]:
            self.populate_income_table()
        if current_widget == self.pages["Expenses"]:
            self.populate_exp_table()
        if current_widget == self.pages["Investments"]:
            self.populate_inv_table()
        if current_widget == self.pages["Debts"]:
            self.populate_debt_table()
        if current_widget == self.pages["Financial Goals"]:
            self.populate_goals_table()


  #blah
    def add_budget_row(self):
        r = self.butt_table.rowCount()
        self.butt_table.insertRow(r)
        self.butt_table.setItem(r, 0, QTableWidgetItem(""))
        self.butt_table.setItem(r, 1, QTableWidgetItem("New Type"))
        self.butt_table.setItem(r, 2, QTableWidgetItem("0"))
        self.butt_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_butt_table(self):
        self._commit_table_edits(self.inv_table)
        rows = self.inv_table.rowCount()
        for i in range(rows):
            id_item = self.inv_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            typ = self.inv_table.item(i, 1).text() if self.inv_table.item(i, 1) else ""
            amount_text = self.inv_table.item(i, 2).text() if self.inv_table.item(i, 2) else "0"
            date = self.inv_table.item(i, 3).text() if self.inv_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = self._parse_amount(amount_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("budget", row_id, (typ, amount, date))
        QMessageBox.information(self, "Saved", "Budget saved.")
        self.refresh_current_page()
   

   
    def populate_income_table(self):
        rows = fetch_month_data("income", self.current_year, self.current_month)
        self.income_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.income_table.setItem(i, 0, id_item)
            self.income_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.income_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.income_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_income_row(self):
        r = self.income_table.rowCount()
        self.income_table.insertRow(r)
        self.income_table.setItem(r, 0, QTableWidgetItem(""))  # new row id
        self.income_table.setItem(r, 1, QTableWidgetItem("New Source"))
        self.income_table.setItem(r, 2, QTableWidgetItem("0"))
        self.income_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_income_table(self):
        self._commit_table_edits(self.income_table)
        rows = self.income_table.rowCount()
        for i in range(rows):
            id_item = self.income_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            source = self.income_table.item(i, 1).text() if self.income_table.item(i, 1) else ""
            amount_text = self.income_table.item(i, 2).text() if self.income_table.item(i, 2) else "0"
            date = self.income_table.item(i, 3).text() if self.income_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = self._parse_amount(amount_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("income", row_id, (source, amount, date))
        QMessageBox.information(self, "Saved", "Income table saved.")
        self.current_nav = "Dashboard"
        self.refresh_current_page()


    def populate_exp_table(self):
        rows = fetch_month_data("expenses", self.current_year, self.current_month)
        self.exp_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exp_table.setItem(i, 0, id_item)
            self.exp_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.exp_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.exp_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_expense_row(self):
        r = self.exp_table.rowCount()
        self.exp_table.insertRow(r)
        self.exp_table.setItem(r, 0, QTableWidgetItem(""))
        self.exp_table.setItem(r, 1, QTableWidgetItem("New Category"))
        self.exp_table.setItem(r, 2, QTableWidgetItem("0"))
        self.exp_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_exp_table(self):
        self._commit_table_edits(self.exp_table)
        rows = self.exp_table.rowCount()
        for i in range(rows):
            id_item = self.exp_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            category = self.exp_table.item(i, 1).text() if self.exp_table.item(i, 1) else ""
            amount_text = self.exp_table.item(i, 2).text() if self.exp_table.item(i, 2) else "0"
            date = self.exp_table.item(i, 3).text() if self.exp_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = self._parse_amount(amount_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("expenses", row_id, (category, amount, date))
        QMessageBox.information(self, "Saved", "Expenses table saved.")
        self.current_nav = "Dashboard"
        self.refresh_current_page()

  
    def populate_inv_table(self):
        rows = fetch_month_data("investments", self.current_year, self.current_month)
        self.inv_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inv_table.setItem(i, 0, id_item)
            self.inv_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.inv_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.inv_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_invest_row(self):
        r = self.inv_table.rowCount()
        self.inv_table.insertRow(r)
        self.inv_table.setItem(r, 0, QTableWidgetItem(""))
        self.inv_table.setItem(r, 1, QTableWidgetItem("New Type"))
        self.inv_table.setItem(r, 2, QTableWidgetItem("0"))
        self.inv_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_inv_table(self):
        self._commit_table_edits(self.inv_table)
        rows = self.inv_table.rowCount()
        for i in range(rows):
            id_item = self.inv_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            typ = self.inv_table.item(i, 1).text() if self.inv_table.item(i, 1) else ""
            amount_text = self.inv_table.item(i, 2).text() if self.inv_table.item(i, 2) else "0"
            date = self.inv_table.item(i, 3).text() if self.inv_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = self._parse_amount(amount_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("investments", row_id, (typ, amount, date))
        QMessageBox.information(self, "Saved", "Investments saved.")
        self.refresh_current_page()

    
    def populate_debt_table(self):
        rows = fetch_month_data("debts", self.current_year, self.current_month)
        self.debt_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.debt_table.setItem(i, 0, id_item)
            self.debt_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.debt_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.debt_table.setItem(i, 3, QTableWidgetItem(str(r[3])))

    def add_debt_row(self):
        r = self.debt_table.rowCount()
        self.debt_table.insertRow(r)
        self.debt_table.setItem(r, 0, QTableWidgetItem(""))
        self.debt_table.setItem(r, 1, QTableWidgetItem("New Debt"))
        self.debt_table.setItem(r, 2, QTableWidgetItem("0"))
        self.debt_table.setItem(r, 3, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_debt_table(self):
        self._commit_table_edits(self.debt_table)
        rows = self.debt_table.rowCount()
        for i in range(rows):
            id_item = self.debt_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            typ = self.debt_table.item(i, 1).text() if self.debt_table.item(i, 1) else ""
            amount_text = self.debt_table.item(i, 2).text() if self.debt_table.item(i, 2) else "0"
            date = self.debt_table.item(i, 3).text() if self.debt_table.item(i, 3) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                amount = self._parse_amount(amount_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("debts", row_id, (typ, amount, date))
        QMessageBox.information(self, "Saved", "Debts saved.")
        self.refresh_current_page()

   
    def populate_goals_table(self):
        rows = fetch_month_data("goals", self.current_year, self.current_month)
        self.goals_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            id_item = QTableWidgetItem(str(r[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.goals_table.setItem(i, 0, id_item)
            self.goals_table.setItem(i, 1, QTableWidgetItem(str(r[1])))
            self.goals_table.setItem(i, 2, QTableWidgetItem(str(r[2])))
            self.goals_table.setItem(i, 3, QTableWidgetItem(str(r[3])))
            self.goals_table.setItem(i, 4, QTableWidgetItem(str(r[4])))

    def add_goal_row(self):
        r = self.goals_table.rowCount()
        self.goals_table.insertRow(r)
        self.goals_table.setItem(r, 0, QTableWidgetItem(""))
        self.goals_table.setItem(r, 1, QTableWidgetItem("New Goal"))
        self.goals_table.setItem(r, 2, QTableWidgetItem("0"))
        self.goals_table.setItem(r, 3, QTableWidgetItem("0"))
        self.goals_table.setItem(r, 4, QTableWidgetItem(f"{self.current_year}-{self.current_month:02d}-01"))

    def save_goals_table(self):
        self._commit_table_edits(self.goals_table)
        rows = self.goals_table.rowCount()
        for i in range(rows):
            id_item = self.goals_table.item(i, 0)
            row_id = int(id_item.text()) if id_item and id_item.text().isdigit() else None
            name = self.goals_table.item(i, 1).text() if self.goals_table.item(i, 1) else ""
            target_text = self.goals_table.item(i, 2).text() if self.goals_table.item(i, 2) else "0"
            progress_text = self.goals_table.item(i, 3).text() if self.goals_table.item(i, 3) else "0"
            date = self.goals_table.item(i, 4).text() if self.goals_table.item(i, 4) else f"{self.current_year}-{self.current_month:02d}-01"
            try:
                target = self._parse_amount(target_text)
                progress = self._parse_amount(progress_text)
                date = self._normalize_date(date)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid data", f"Row {i+1}: {exc}")
                return
            save_row("goals", row_id, (name, target, progress, date))
        QMessageBox.information(self, "Saved", "Goals saved.")
        self.refresh_current_page()

    #delete row
    def delete_income_row(self):
        self._delete_selected_row(self.income_table, "income")

    def delete_expense_row(self):
        self._delete_selected_row(self.exp_table, "expenses")

    def delete_invest_row(self):
        self._delete_selected_row(self.inv_table, "investments")

    def delete_debt_row(self):
        self._delete_selected_row(self.debt_table, "debts")

    def delete_goal_row(self):
        self._delete_selected_row(self.goals_table, "goals")

    def delete_budget_row(self):
        self._delete_selected_row(self.butt_table, "budget")

    def _delete_selected_row(self, table_widget: QTableWidget, db_table: str):
        """Common helper: delete selected row from table + database"""
        row = table_widget.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Row Selected", "Please click a row to delete first.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                   "Are you sure you want to permanently delete this row?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete from database if it has an id
        id_item = table_widget.item(row, 0)
        if id_item and id_item.text().isdigit():
            row_id = int(id_item.text())
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(f"DELETE FROM {db_table} WHERE id = ?", (row_id,))
            conn.commit()
            conn.close()

        # Remove from ui table
        table_widget.removeRow(row)
        QMessageBox.information(self, "Deleted", "Row has been deleted.")


    def stylesheet(self):
        return """
        QMainWindow { background: #0f1720; color: #e6eef6; }
        #nav { background: #071126; border-right: 1px solid #1f2a37; }
        QPushButton { background: transparent; color: #cfe6ff; border: none; padding: 8px; text-align: left; }
        QPushButton:hover { background: #0b2a44; }
        QPushButton:checked { background: #0f4b6f; color: white; font-weight: bold; }
        QFrame#card { background: #0b2233; border-radius: 8px; padding: 12px; margin: 6px; }
        QLabel#card_title { color: #9fbcd8; font-size: 12px; }
        QLabel#card_value { color: #ffffff; font-size: 20px; font-weight: bold; }
        QLabel#profile { color: #cfe6ff; font-weight: bold; }
        QLabel#notif { color: #ffcccb; font-weight: bold; }
        QLabel#ranking { color: #dbefff; }
        QLabel#sidebar_name { color: #eaf6ff; font-weight: bold; font-size: 13px; }
        QLabel#sidebar_role { color: #9fbcd8; font-size: 11px; margin-bottom: 8px; }
        QFrame#profile_circle { margin-bottom: 6px; }
        QTableWidget { background: #071826; color: #e6eef6; gridline-color: #123; }
        QHeaderView::section { background: #0b2a3a; color: #dbefff; padding: 6px; }
        """

    def nav_button_style(self, active):
        if active:
            return "background:#0f4b6f; color:white; font-weight:bold; padding:8px;"
        return "background:transparent; color:#cfe6ff; padding:8px;"

    def month_button_style(self, active):
        if active:
            return "background:#1f6f8f; color:white; padding:6px; border-radius:4px;"
        return "background:transparent; color:#cfe6ff; padding:6px;"

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.showNormal()
            self.fullscreen = False
        else:
            self.showFullScreen()
            self.fullscreen = True


def main():
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
