from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "expenses.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            monthly_budget REAL NOT NULL
        )
    """)

    existing_budget = connection.execute(
        "SELECT * FROM settings WHERE id = 1"
    ).fetchone()

    if existing_budget is None:
        connection.execute(
            "INSERT INTO settings (id, monthly_budget) VALUES (1, 5000)"
        )

    connection.commit()
    connection.close()


@app.route("/")
def home():

    connection = get_db()

    expenses = connection.execute("""
        SELECT * FROM expenses
        ORDER BY id DESC
    """).fetchall()

    total_spent = connection.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """).fetchone()[0]

    budget = connection.execute("""
        SELECT monthly_budget
        FROM settings
        WHERE id = 1
    """).fetchone()["monthly_budget"]

    category_data = connection.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """).fetchall()

    connection.close()

    categories = []

    for category in category_data:

        percentage = 0

        if total_spent > 0:
            percentage = (category["total"] / total_spent) * 100

        categories.append({
            "category": category["category"],
            "total": category["total"],
            "percentage": percentage
        })

    remaining = budget - total_spent

    return render_template(
        "index.html",
        expenses=expenses,
        total_spent=total_spent,
        remaining=remaining,
        budget=budget,
        category_data=categories
    )


@app.route("/add", methods=["POST"])
def add_expense():

    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form["description"]

    date = datetime.now().strftime("%d %b %Y")

    connection = get_db()

    connection.execute("""
        INSERT INTO expenses
        (amount, category, description, date)
        VALUES (?, ?, ?, ?)
    """, (amount, category, description, date))

    connection.commit()
    connection.close()

    return redirect("/")


@app.route("/budget", methods=["POST"])
def update_budget():

    budget = request.form["budget"]

    connection = get_db()

    connection.execute("""
        UPDATE settings
        SET monthly_budget = ?
        WHERE id = 1
    """, (budget,))

    connection.commit()
    connection.close()

    return redirect("/")


@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):

    connection = get_db()

    connection.execute("""
        DELETE FROM expenses
        WHERE id = ?
    """, (expense_id,))

    connection.commit()
    connection.close()

    return redirect("/")


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
