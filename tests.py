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

    def test_add_transaction_valid(self):
        response = self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01",
            "description": "Groceries"
        })
        self.assertEqual(response.status_code, 201)

    def test_add_transaction_invalid_amount(self):
        response = self.app.post("/transactions", json={
            "amount": -100.0,
            "category": "Food",
            "date": "2024-12-01"
        })
        self.assertEqual(response.status_code, 400)

    def test_add_budget_valid(self):
        response = self.app.post("/budgets", json={
            "category": "Food",
            "budget_limit": 300.0
        })
        self.assertEqual(response.status_code, 201)

    def test_add_budget_invalid_limit(self):
        response = self.app.post("/budgets", json={
            "category": "Food",
            "budget_limit": -100.0
        })
        self.assertEqual(response.status_code, 400)

    def test_generate_report_empty(self):
        response = self.app.get("/generate_report")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No data", response.json["message"])

    def test_generate_report_valid(self):
        self.app.post("/transactions", json={
            "amount": 100.0,
            "category": "Food",
            "date": "2024-12-01"
        })
        response = self.app.get("/generate_report")
        self.assertEqual(response.status_code, 200)
        self.assertIn("report.png", response.json["message"])


if __name__ == "__main__":
    unittest.main()
