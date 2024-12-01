from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)

DB_FILE = "finance_tracker.db"


def init_db():
    """Initialize the database tables."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            budget_limit REAL NOT NULL
        )
        """)
        conn.commit()


init_db()


def execute_query(query, params=(), fetch=False):
    """Helper function to execute SQL queries."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        conn.commit()


def validate_transaction(data):
    """Validate transaction input data."""
    required_fields = {"amount", "category", "date"}
    missing_fields = required_fields - data.keys()
    if missing_fields:
        return False, f"Missing required field(s): {', '.join(missing_fields)}"
    try:
        datetime.strptime(data["date"], "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."
    return True, None


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Finance Tracker</title>
</head>
<body>
    <h1>Personal Finance Tracker</h1>
    <h2>Transactions</h2>
    <ul>
        {% for transaction in transactions %}
        <li>
            <strong>${{ transaction[1] }}</strong> ({{ transaction[2] }}) on {{ transaction[3] }}
            {% if transaction[4] %}
            - {{ transaction[4] }}
            {% endif %}
        </li>
        {% endfor %}
    </ul>
    <h2>Budgets</h2>
    <ul>
        {% for budget in budgets %}
        <li>{{ budget[1] }}: ${{ budget[2] }} limit</li>
        {% endfor %}
    </ul>
    <a href="/generate_report">Generate Report</a>
</body>
</html>
"""


@app.route("/")
def index():
    """Home page displaying transactions and budgets."""
    transactions = execute_query("SELECT * FROM transactions", fetch=True)
    budgets = execute_query("SELECT * FROM budgets", fetch=True)
    return render_template_string(HTML_TEMPLATE, transactions=transactions, budgets=budgets)


@app.route("/transactions", methods=["POST"])
def add_transaction():
    """Add a new transaction."""
    data = request.json
    valid, error = validate_transaction(data)
    if not valid:
        return jsonify({"error": error}), 400
    execute_query("""
        INSERT INTO transactions (amount, category, date, description)
        VALUES (?, ?, ?, ?)
        """, (data["amount"], data["category"], data["date"], data.get("description")))
    return jsonify({"message": "Transaction added"}), 201


@app.route("/transactions", methods=["GET"])
def get_transactions():
    """Retrieve all transactions."""
    transactions = execute_query("SELECT * FROM transactions", fetch=True)
    return jsonify(transactions)


@app.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    """Delete a transaction by ID."""
    execute_query("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    return jsonify({"message": "Transaction deleted"}), 200


@app.route("/budgets", methods=["POST"])
def add_budget():
    """Add or update a budget."""
    data = request.json
    if "category" not in data or "budget_limit" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    execute_query("""
        INSERT OR REPLACE INTO budgets (category, budget_limit)
        VALUES (?, ?)
        """, (data["category"], data["budget_limit"]))
    return jsonify({"message": "Budget added/updated"}), 201


@app.route("/budgets", methods=["GET"])
def get_budgets():
    """Retrieve all budgets."""
    budgets = execute_query("SELECT * FROM budgets", fetch=True)
    return jsonify(budgets)


@app.route("/budgets/check", methods=["GET"])
def check_budgets():
    """Check spending against budgets."""
    query = """
        SELECT budgets.category, budgets.budget_limit, COALESCE(SUM(transactions.amount), 0)
        FROM budgets
        LEFT JOIN transactions ON budgets.category = transactions.category
        GROUP BY budgets.category
    """
    budget_status = {}
    for row in execute_query(query, fetch=True):
        category, limit, spent = row
        budget_status[category] = {"limit": limit, "spent": spent, "remaining": limit - spent}
    return jsonify(budget_status)


@app.route("/generate_report", methods=["GET"])
def generate_report():
    """Generate a spending report."""
    transactions = execute_query("""
        SELECT category, SUM(amount) FROM transactions GROUP BY category
    """, fetch=True)
    category_totals = {row[0]: row[1] for row in transactions}
    if not category_totals:
        return jsonify({"message": "No data to generate report"}), 200

    # Generate Pie Chart
    categories = list(category_totals.keys())
    totals = list(category_totals.values())
    plt.figure(figsize=(6, 6))
    plt.pie(totals, labels=categories, autopct='%1.1f%%')
    plt.title("Spending by Category")
    plt.savefig("report.png")

    return jsonify({"message": "Report generated: report.png"})


if __name__ == "__main__":
    app.run(debug=True)
