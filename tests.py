import unittest
import json
from pft import app, init_db, DB_FILE
import os

class TestPersonalFinanceTracker(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()

    def tearDown(self):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

    def test_add_transaction(self):
        response = self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        self.assertEqual(response.status_code, 201)

    def test_get_transactions(self):
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        response = self.app.get("/transactions")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)

    def test_add_budget(self):
        response = self.app.post("/budgets", json={
            "category": "Food",
            "budget_limit": 300.0
        })
        self.assertEqual(response.status_code, 201)

    def test_get_budgets(self):
        self.app.post("/budgets", json={"category": "Food", "budget_limit": 300.0})
        response = self.app.get("/budgets")
        self.assertEqual(response.status_code, 200)

    def test_budget_check(self):
        self.app.post("/budgets", json={"category": "Food", "budget_limit": 300.0})
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        response = self.app.get("/budgets/check")
        self.assertEqual(response.status_code, 200)

    def test_delete_transaction(self):
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        response = self.app.delete("/transactions/1")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
