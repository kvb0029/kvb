import unittest
import json
from pft import app, init_db, DB_FILE
import sqlite3
import os


class TestPersonalFinanceTracker(unittest.TestCase):
    def setUp(self):
        # Initialize the app and testing client
        self.app = app.test_client()
        self.app.testing = True
        init_db()

    def tearDown(self):
        # Remove the database after each test
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

    def test_add_transaction(self):
        # Add a transaction
        data = {
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        }
        response = self.app.post("/transactions", json=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "Transaction added")

    def test_add_transaction_invalid_date(self):
        # Add a transaction with an invalid date
        data = {
            "amount": 50.0,
            "category": "Entertainment",
            "date": "12-01-2024",  # Invalid format
            "description": "Movies"
        }
        response = self.app.post("/transactions", json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid date format", response.json["error"])

    def test_get_transactions(self):
        # Add a sample transaction
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })

        # Retrieve all transactions
        response = self.app.get("/transactions")
        self.assertEqual(response.status_code, 200)
        transactions = response.json
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0][1], 100.0)

    def test_add_budget(self):
        # Add a budget
        data = {"category": "Food", "budget_limit": 300.0}
        response = self.app.post("/budgets", json=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"], "Budget added/updated")

    def test_get_budgets(self):
        # Add a sample budget
        self.app.post("/budgets", json={"category": "Food", "budget_limit": 300.0})

        # Retrieve all budgets
        response = self.app.get("/budgets")
        self.assertEqual(response.status_code, 200)
        budgets = response.json
        self.assertEqual(len(budgets), 1)
        self.assertEqual(budgets[0][1], "Food")

    def test_generate_report(self):
        # Add sample transactions
        transactions = [
            {"amount": 100.0, "category": "Food", "date": "2024-12-01", "description": "Groceries"},
            {"amount": 50.0, "category": "Entertainment", "date": "2024-12-02", "description": "Movies"}
        ]
        for transaction in transactions:
            self.app.post("/transactions", json=transaction)

        # Generate report
        response = self.app.get("/generate_report")
        self.assertEqual(response.status_code, 200)
        self.assertIn("report.png", response.json["message"])

    def test_budget_check(self):
        # Add budgets and transactions
        self.app.post("/budgets", json={"category": "Food", "budget_limit": 300.0})
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })

        # Check budget status
        response = self.app.get("/budgets/check")
        self.assertEqual(response.status_code, 200)
        budgets = response.json
        self.assertIn("Food", budgets)
        self.assertEqual(budgets["Food"]["spent"], 100.0)
        self.assertEqual(budgets["Food"]["remaining"], 200.0)

    def test_delete_transaction(self):
        # Add a transaction
        response = self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        self.assertEqual(response.status_code, 201)

        # Delete the transaction
        response = self.app.delete("/transactions/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "Transaction deleted")

        # Verify the transaction is deleted
        response = self.app.get("/transactions")
        transactions = response.json
        self.assertEqual(len(transactions), 0)


if __name__ == "__main__":
    unittest.main()
