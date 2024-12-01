from flask import Flask, request, jsonify, render_template_string
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)

# Database setup
DB_FILE = "finance_tracker.db"

def init_db():
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

# Utility Functions
def validate_transaction(data):
    required_fields = ["amount", "category", "date"]
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    try:
        datetime.strptime(data["date"], "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD."
    return True, None

# Embedded HTML and CSS Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Finance Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }
        header {
            background-color: #007bff;
            color: #fff;
            padding: 20px;
            text-align: center;
        }
        main {
            padding: 20px;
            max-width: 800px;
            margin: 20px auto;
            background: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            color: #007bff;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
            padding: 10px;
            background: #f1f1f1;
            border-radius: 5px;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            text-decoration: none;
            color: #fff;
            background: #007bff;
            border-radius: 5px;
        }
        a:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <header>
        <h1>Personal Finance Tracker</h1>
    </header>
    <main>
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
    </main>
</body>
</html>
"""

# API Endpoints
@app.route("/")
def index():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        cursor.execute("SELECT * FROM budgets")
        budgets = cursor.fetchall()
    return render_template_string(HTML_TEMPLATE, transactions=transactions, budgets=budgets)

@app.route("/transactions", methods=["POST"])
def add_transaction():
    data = request.json
    valid, error = validate_transaction(data)
    if not valid:
        return jsonify({"error": error}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO transactions (amount, category, date, description)
        VALUES (?, ?, ?, ?)
        """, (data["amount"], data["category"], data["date"], data.get("description")))
        conn.commit()
    return jsonify({"message": "Transaction added"}), 201

@app.route("/budgets", methods=["POST"])
def add_budget():
    data = request.json
    if "category" not in data or "budget_limit" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO budgets (category, budget_limit)
        VALUES (?, ?)
        """, (data["category"], data["budget_limit"]))
        conn.commit()
    return jsonify({"message": "Budget added/updated"}), 201

@app.route("/generate_report", methods=["GET"])
def generate_report():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT category, SUM(amount) FROM transactions GROUP BY category
        """)
        category_totals = {row[0]: row[1] for row in cursor.fetchall()}

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
