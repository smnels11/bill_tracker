# Library Imports
from datetime import date

import pandas as pd
import streamlit as st

from utils import (
    add_bill,
    delete_bill,
    get_paid_bills,
    get_unpaid_bills,
    mark_paid,
)

# Page Config

st.set_page_config(page_title="Bill Tracker", layout="centered")

st.title("Bill Tracker")

# Summary Metrics

# Example bill data; replace with your own values
bill_dict = {
    "Bill": [
        "Rent",
        "Electric",
        "Internet",
        "Credit Card",
        "Student Loan",
    ],
    "Payment Due Date": ["1st", "10th", "15th", "20th", "25th"],
    "Minimum Payment": [
        "$1200.00",
        "variable",
        "$75.00",
        "$50.00",
        "$200.00",
    ],
}

bill_df = pd.DataFrame(bill_dict)

st.dataframe(
    bill_df,
    column_config={
        "Bill": st.column_config.Column("Bill", alignment="left"),
        "Payment Due Date": st.column_config.Column(
            "Payment Due Date", alignment="right"
        ),
        "Minimum Payment": st.column_config.Column(
            "Payment", alignment="right"
        ),
    },
    hide_index=True,
)

st.divider()

# Unpaid Bills

st.subheader("Unpaid Bills")

# Cols of unpaid_df:
# id
# bill_name
# due_date
# recurs_monthly
unpaid_df = get_unpaid_bills()

if unpaid_df.empty:
    st.info("No unpaid bills. Add one above.")
else:
    today = date.today()

    for _, row in unpaid_df.iterrows():
        due = row["due_date"]
        days_delta = (due - today).days

        if days_delta < 0:
            badge_0 = "🔴"
            badge_f = f"{abs(days_delta)}d overdue!"
        elif days_delta == 0:
            badge_0 = "🟠"
            badge_f = "Due today!"
        elif days_delta <= 7:
            badge_0 = "🟡"
            badge_f = f"Due in {days_delta}d!"
        else:
            badge_0 = "🟢"
            badge_f = f"Due in {days_delta}d"

        label = f"{badge_0} **{row['bill_name']}** -- {badge_f} ({due})"

        with st.expander(label):
            amount_paid = st.number_input(
                "Amount paid ($)",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                key=f"amount_{row['id']}",
            )

            c1, c2 = st.columns(2)

            if c1.button("✅ Mark as Paid", key=f"pay_{row['id']}"):
                mark_paid(
                    row["id"], bool(row["recurs_monthly"]), due, amount_paid
                )
                st.rerun()
            if c2.button("🗑 Delete", key=f"del_{row['id']}"):
                delete_bill(row["id"])
                st.rerun()


st.divider()


# Payment History

with st.expander("Payment history (last 50)"):
    paid_df = get_paid_bills()
    if paid_df.empty:
        st.write("No payments recorded yet.")
    else:
        paid_df["paid_at"] = pd.to_datetime(paid_df["paid_at"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        paid_df["amount_paid"] = paid_df["amount_paid"].map("${:,.2f}".format)
        paid_df = paid_df.rename(
            columns={
                "bill_name": "Bill",
                "amount_paid": "Amount Paid",
                "due_date": "Was Due",
                "paid_at": "Paid At",
            }
        )
        st.dataframe(
            paid_df[["Bill", "Amount Paid", "Was Due", "Paid At"]],
            use_container_width=True,
            hide_index=True,
        )

st.divider()

# Add a New Bill

with st.expander("➕ Add a new bill"):
    bill_name = st.text_input(
        "Bill name", placeholder="e.g. Electric, Internet, Rent"
    )
    due_date = st.date_input("Due date", value=date.today())
    recurs_monthly = st.checkbox(
        "Repeats monthly",
        value=True,
        help="Auto-creates next month's entry when marked paid",
    )

    if st.button("Add Bill", type="primary"):
        if not bill_name.strip():
            st.warning("Give the bill a name.")
        else:
            add_bill(bill_name.strip(), due_date, recurs_monthly)
            st.success(f"Added **{bill_name}** — due {due_date}.")
            st.rerun()
