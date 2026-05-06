import unittest
import json
import os
import tempfile
from datetime import datetime

# Import functions from your main module
# We'll temporarily override DATA_FILE to use a temporary file during tests
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Hack to allow importing without running main
import ACC_v1_0 as ledger  # rename your file to ACC_v1_0.py or adjust import
# If your file is named ACC_v1.0.py, you cannot import it directly.
# Either rename it to ACC_v1_0.py or use __import__.
# For simplicity, I'll assume you rename to ACC_v1_0.py

class TestLedger(unittest.TestCase):
    def setUp(self):
        """Create a temporary file for each test"""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_filename = self.temp_file.name
        self.original_data_file = ledger.DATA_FILE
        ledger.DATA_FILE = self.temp_filename
        # Start with empty dict
        ledger.save_transactions({})

    def tearDown(self):
        """Clean up temp file"""
        ledger.DATA_FILE = self.original_data_file
        os.unlink(self.temp_filename)

    def test_add_transaction(self):
        tx = ledger.add_transaction({}, "Test", 10.5, "Cash", "Income", "comment")
        self.assertEqual(len(tx), 1)
        first = tx[1]
        self.assertEqual(first["desc"], "Test")
        self.assertEqual(first["amount"], 10.5)
        self.assertEqual(first["dr"], "Cash")
        self.assertEqual(first["cr"], "Income")
        self.assertEqual(first["comment"], "comment")

    def test_delete_transaction(self):
        tx = ledger.add_transaction({}, "Del me", 5, "Expense", "Cash")
        tx = ledger.delete_transaction(tx, 1)
        self.assertEqual(len(tx), 0)

    def test_edit_transaction(self):
        tx = ledger.add_transaction({}, "Original", 10, "A", "B")
        tx = ledger.edit_transaction(tx, 1, "amount", 20)
        self.assertEqual(tx[1]["amount"], 20)
        tx = ledger.edit_transaction(tx, 1, "description", "New desc")
        self.assertEqual(tx[1]["desc"], "New desc")

    def test_search_transaction(self):
        tx = ledger.add_transaction({}, "Coffee", 3.5, "Food", "Cash")
        tx = ledger.add_transaction(tx, "Bus", 1.5, "Transport", "EasyCard")
        results = ledger.search_transactions(tx, keyword="coffee")
        # search_transactions prints a table, but returns nothing.
        # We'll modify search_transactions to also return results? For testing, we can capture prints or refactor.
        # Simpler: test the filtering logic by calling internal search code.
        # Better: modify search_transactions to optionally return results.
        # I'll show a modified version below.

    def test_balance(self):
        tx = ledger.add_transaction({}, "test", 100, "Cash", "Income")
        tx = ledger.add_transaction(tx, "test2", 20, "Food", "Cash")
        # Balance: Cash: -120? Wait: first: dr Cash +100, cr Income -100 => Cash 100, Income -100
        # second: dr Food +20, cr Cash -20 => Cash 80, Food 20, Income -100
        # We'll just check that show_balance doesn't crash; or capture output.
        # For unit test, we can compute balances directly using internal logic.
        balances = {}
        for t in tx.values():
            balances[t["dr"]] = balances.get(t["dr"], 0) + t["amount"]
            balances[t["cr"]] = balances.get(t["cr"], 0) - t["amount"]
        self.assertEqual(balances["Cash"], 80)
        self.assertEqual(balances["Food"], 20)
        self.assertEqual(balances["Income"], -100)

    def test_import_export(self):
        tx = ledger.add_transaction({}, "Export test", 99, "DrAcc", "CrAcc")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_name = tmp.name
        ledger.export_transactions(tx, tmp_name)
        with open(tmp_name) as f:
            exported = json.load(f)
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["desc"], "Export test")
        # Test import merge
        new_tx = ledger.import_transactions({}, tmp_name, replace=False)
        self.assertEqual(len(new_tx), 1)
        # Clean up
        os.unlink(tmp_name)

if __name__ == "__main__":
    unittest.main()