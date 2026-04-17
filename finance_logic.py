import sqlite3
from typing import Dict, List, Tuple

DB_NAME = "finance.db"
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def _sum_for_month(cursor: sqlite3.Cursor, table: str, amount_col: str, year: int, month: int) -> float:
    month_str = f"{year}-{month:02d}%"
    cursor.execute(
        f"SELECT COALESCE(SUM({amount_col}), 0) FROM {table} WHERE date LIKE ?",
        (month_str,),
    )
    return float(cursor.fetchone()[0] or 0)


def _series_for_table(table: str, amount_col: str, year: int) -> List[float]:
    conn = _connect()
    cursor = conn.cursor()
    values = [_sum_for_month(cursor, table, amount_col, year, month) for month in range(1, 13)]
    conn.close()
    return values


def get_yearly_category_series(category: str, year: int) -> Dict[str, List[float]]:
    """
    Returns Jan-Dec totals for selected dashboard category.
    """
    if category == "Income":
        values = _series_for_table("income", "amount", year)
    elif category == "Expenses":
        values = _series_for_table("expenses", "amount", year)
    elif category == "Investments":
        values = _series_for_table("investments", "amount", year)
    elif category == "Debts":
        values = _series_for_table("debts", "amount", year)
    elif category == "Financial Goals":
        values = _series_for_table("goals", "progress", year)
    else:  # Budgeting
        income_vals = _series_for_table("income", "amount", year)
        expense_vals = _series_for_table("expenses", "amount", year)
        values = [inc - exp for inc, exp in zip(income_vals, expense_vals)]

    return {"labels": MONTH_LABELS, "values": values}


def get_monthly_breakdown(category: str, year: int, month: int) -> Dict[str, List[float]]:
    """
    Returns per-item breakdown for pie/ranking in selected month.
    """
    conn = _connect()
    cursor = conn.cursor()
    month_like = f"{year}-{month:02d}%"

    if category == "Income":
        cursor.execute(
            "SELECT source, COALESCE(SUM(amount), 0) FROM income WHERE date LIKE ? "
            "GROUP BY source ORDER BY SUM(amount) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()
    elif category == "Expenses":
        cursor.execute(
            "SELECT category, COALESCE(SUM(amount), 0) FROM expenses WHERE date LIKE ? "
            "GROUP BY category ORDER BY SUM(amount) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()
    elif category == "Investments":
        cursor.execute(
            "SELECT type, COALESCE(SUM(amount), 0) FROM investments WHERE date LIKE ? "
            "GROUP BY type ORDER BY SUM(amount) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()
    elif category == "Debts":
        cursor.execute(
            "SELECT type, COALESCE(SUM(amount), 0) FROM debts WHERE date LIKE ? "
            "GROUP BY type ORDER BY SUM(amount) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()
    elif category == "Financial Goals":
        cursor.execute(
            "SELECT name, COALESCE(SUM(progress), 0) FROM goals WHERE date LIKE ? "
            "GROUP BY name ORDER BY SUM(progress) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()
    else:  # Budgeting -> expense category breakdown only
        cursor.execute(
            "SELECT category, COALESCE(SUM(amount), 0) FROM expenses WHERE date LIKE ? "
            "GROUP BY category ORDER BY SUM(amount) DESC",
            (month_like,),
        )
        rows = cursor.fetchall()

    conn.close()
    labels = [str(r[0]) for r in rows]
    values = [float(r[1] or 0) for r in rows]
    return {"labels": labels, "values": values}


def get_ranking_text(category: str, labels: List[str], values: List[float]) -> str:
    if not labels or not values:
        return f"No {category.lower()} data"
    pairs: List[Tuple[str, float]] = sorted(zip(labels, values), key=lambda x: -x[1])[:5]
    title = f"{category} Ranking"
    body = "<br>".join([f"{name}: ${value:,.2f}" for name, value in pairs])
    return f"<b>{title}</b><br>{body}"

