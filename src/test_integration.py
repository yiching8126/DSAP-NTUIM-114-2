import unittest
import tempfile
import os
import json
from datetime import datetime
import sys

import main as ledger

class TestLedgerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_data_file = ledger.DATA_FILE
        self.original_budget_file = ledger.BUDGET_FILE
        self.original_script_dir = ledger.SCRIPT_DIR

        ledger.SCRIPT_DIR = self.temp_dir.name
        ledger.DATA_FILE = os.path.join(self.temp_dir.name, "ledger_dict.json")
        ledger.BUDGET_FILE = os.path.join(self.temp_dir.name, "budget.json")

        ledger.undo_stack.clear()
        ledger.redo_stack.clear()

        self.transactions = {}
        ledger.save_transactions(self.transactions)

    def tearDown(self):
        ledger.DATA_FILE = self.original_data_file
        ledger.BUDGET_FILE = self.original_budget_file
        ledger.SCRIPT_DIR = self.original_script_dir
        self.temp_dir.cleanup()

    def test_add_and_list(self):
        self.transactions = ledger.add_transaction(self.transactions, "Coffee", 3.5, "Food", "Cash", "Morning coffee")
        self.transactions = ledger.add_transaction(self.transactions, "Bus ticket", 1.5, "Transport", "EasyCard", "")
        saved = ledger.load_transactions()
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[1]["desc"], "Coffee")
        self.assertEqual(saved[2]["amount"], 1.5)

    def test_delete_and_reindex(self):
        self.transactions = ledger.add_transaction(self.transactions, "First", 10, "Cash", "Income")
        self.transactions = ledger.add_transaction(self.transactions, "Second", 20, "Cash", "Income")
        self.transactions = ledger.add_transaction(self.transactions, "Third", 30, "Cash", "Income")
        self.assertEqual(len(self.transactions), 3)
        self.transactions = ledger.delete_transaction(self.transactions, 2)
        saved = ledger.load_transactions()
        self.assertEqual(len(saved), 2)
        self.assertIn(1, saved)
        self.assertIn(2, saved)
        self.assertEqual(saved[1]["desc"], "First")
        self.assertEqual(saved[2]["desc"], "Third")

    def test_undo_redo_workflow(self):
        self.transactions = ledger.add_transaction(self.transactions, "Rent", 1000, "Rent", "Cash")
        self.transactions = ledger.edit_transaction(self.transactions, 1, "amount", 1200)
        self.assertEqual(self.transactions[1]["amount"], 1200)
        self.transactions = ledger.undo(self.transactions)
        self.assertEqual(self.transactions[1]["amount"], 1000)
        self.transactions = ledger.redo(self.transactions)
        self.assertEqual(self.transactions[1]["amount"], 1200)

    def test_budget_and_export_import(self):
        ledger.set_budget("Food", 200)
        self.transactions = ledger.add_transaction(self.transactions, "Groceries", 45.0, "Food", "Cash")

        budgets = ledger.load_budgets()
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        spending = 0
        for tx in self.transactions.values():
            tx_date = datetime.strptime(tx["date"], "%Y-%m-%d %H:%M:%S")
            if tx_date >= start_of_month and tx["dr"] in budgets:
                spending += tx["amount"]
        self.assertEqual(spending, 45.0)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            export_file = tmp.name
        ledger.export_transactions(self.transactions, export_file)

        self.transactions = {}
        ledger.save_transactions(self.transactions)
        self.assertEqual(len(ledger.load_transactions()), 0)

        self.transactions = ledger.import_transactions(self.transactions, export_file, replace=False)
        imported = ledger.load_transactions()
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[1]["desc"], "Groceries")

        os.unlink(export_file)

if __name__ == "__main__":
    unittest.main()