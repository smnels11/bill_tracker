"""
utils.py

Database utility module for bill_tracker app.

Handles all interactions with the Postgres database. Imported by
app.py, keeping database functions separate from the Streamlit UI layer.

Database
--------
Connects to a Postgres instance using credentials injected as environment
variables by Docker Compose:
    POSTGRES_USER
    POSTGRES_PASSWORD
    POSTGRES_HOST
    POSTGRES_DB

Functions
---------
add_bill        : Insert a new unpaid bill
get_unpaid_bills: Fetch all unpaid bills ordered by due date
get_paid_bills  : Fetch the 50 most recently paid bills
mark_paid       : Mark a bill paid, record amount, and roll forward if recurring
delete_bill     : Delete a single bill entry by primary key
"""

# Library Imports
import calendar
import os
from datetime import date

import pandas as pd
from sqlalchemy import create_engine, text

# Database Setup
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)


# Database Functions


def add_bill(name: str, due_date: date, recurs_monthly: bool) -> None:
    """
    Insert a new unpaid bill into the database.

    Parameters
    ----------
    name : str
        Display name of the bill (e.g. "Rent", "BGE").
    due_date : date
        The date this bill is due.
    recurs_monthly : bool
        If True, a new entry for the following month is automatically
        created when this bill is marked paid.
    """

    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO bills (bill_name, due_date, recurs_monthly)
            VALUES (:name, :due_date, :recurs_monthly)
            """),
            {
                "name": name,
                "due_date": due_date,
                "recurs_monthly": recurs_monthly,
            },
        )


def get_unpaid_bills() -> pd.DataFrame:
    """
    Fetch all unpaid bills ordered by due date ascending (soonest first).

    Returns
    -------
    pd.DataFrame
        Columns: id, bill_name, due_date, recurs_monthly.
    """

    with engine.connect() as conn:
        return pd.read_sql(
            text("""
            SELECT id, bill_name, due_date, recurs_monthly
            FROM bills
            WHERE is_paid = FALSE
            ORDER BY due_date ASC
            """),
            conn,
        )


def get_paid_bills() -> pd.DataFrame:
    """
    Fetch the 50 most recently paid bills ordered by payment timestamp
    descending.

    Returns
    -------
    pd.DataFrame
        Columns: bill_name, amount_paid, due_date, paid_at.
    """

    with engine.connect() as conn:
        return pd.read_sql(
            text("""
            SELECT bill_name, amount_paid, due_date, paid_at
            FROM bills
            WHERE is_paid = TRUE
            ORDER BY paid_at DESC
            LIMIT 50
            """),
            conn,
        )


def mark_paid(
    bill_id: int, recurs_monthly: bool, due_date: date, amount_paid: float
) -> None:
    """
    Mark a bill as paid and record the amount paid.

    If the bill recurs monthly, a new unpaid entry is automatically inserted
    with the due date rolled forward by one month.

    Parameters
    ----------
    bill_id : int
        Primary key of the bill row to update.
    recurs_monthly : bool
        Whether to insert a new entry for the following month.
    due_date : date
        Due date of the current bill, used to calculate the next due date.
    amount_paid : float
        The actual amount paid, recorded against this entry.
    """

    with engine.begin() as conn:
        conn.execute(
            text("""
            UPDATE bills
            SET is_paid = TRUE, paid_at = NOW(), amount_paid = :amount_paid
            WHERE id = :id
            """),
            {"id": bill_id, "amount_paid": amount_paid},
        )

        if recurs_monthly:
            if due_date.month == 12:
                next_year, next_month = due_date.year + 1, 1
            else:
                next_year, next_month = due_date.year, due_date.month + 1

            last_day = calendar.monthrange(next_year, next_month)[1]
            next_due = date(next_year, next_month, min(due_date.day, last_day))

            conn.execute(
                text("""
                INSERT INTO bills (bill_name, due_date, recurs_monthly)
                SELECT bill_name, :next_due, TRUE
                FROM bills
                WHERE id = :id
                """),
                {"next_due": next_due, "id": bill_id},
            )


def delete_bill(bill_id: int) -> None:
    """
    Permanently delete a single bill entry by its primary key.

    This only removes the one row matching bill_id — it does not affect
    any other entries for the same bill name.

    Parameters
    ----------
    bill_id : int
        Primary key of the bill row to delete.
    """

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM bills WHERE id = :id"), {"id": bill_id})
