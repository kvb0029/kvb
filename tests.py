import unittest
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

    def test_invalid_transaction_negative_amount(self):
        response = self.app.post("/transactions", json={
            "amount": -100.0,
            "category": "Food",
            "date": "2024-12-01"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("positive number", response.json["error"])

    def test_budget_zero_limit(self):
        response = self.app.post("/budgets", json={
            "category": "Food",
            "budget_limit": 0.0
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("positive number", response.json["error"])

    def test_check_budgets(self):
        self.app.post("/budgets", json={"category": "Food", "budget_limit": 300.0})
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        response = self.app.get("/budgets/check")
        self.assertEqual(response.status_code, 200)
        budgets = response.json
        self.assertIn("Food", budgets)
        self.assertEqual(budgets["Food"]["remaining"], 200.0)


if __name__ == "__main__":
    unittest.main()
