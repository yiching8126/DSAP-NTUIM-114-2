import pytest
from ledger import Ledger, Transaction

def test_add_transaction(ledger):
    tx = ledger.add_transaction("Coffee", 3.5, "Food", "Cash")
    assert tx.id == 1
    assert tx.desc == "Coffee"
    assert ledger.get_transactions()[0].amount == 3.5

def test_delete_transaction(ledger):
    tx1 = ledger.add_transaction("First", 1, "A", "B")
    tx2 = ledger.add_transaction("Second", 2, "C", "D")
    assert len(ledger.get_transactions()) == 2
    assert ledger.delete_transaction(tx1.id) is True
    assert len(ledger.get_transactions()) == 1
    # IDs are not rebuilt automatically
    assert ledger.get_transactions()[0].id == 2

def test_delete_nonexistent(ledger):
    assert ledger.delete_transaction(999) is False

def test_edit_transaction(ledger):
    tx = ledger.add_transaction("Old", 5, "X", "Y")
    assert ledger.edit_transaction(tx.id, "desc", "New") is True
    assert ledger._transactions[tx.id].desc == "New"
    ledger.undo()
    assert ledger._transactions[tx.id].desc == "Old"

def test_undo_redo(ledger):
    ledger.add_transaction("First", 1, "A", "B")
    ledger.add_transaction("Second", 2, "C", "D")
    assert len(ledger.get_transactions()) == 2
    ledger.undo()
    assert len(ledger.get_transactions()) == 1
    assert ledger.get_transactions()[0].desc == "First"
    ledger.redo()
    assert len(ledger.get_transactions()) == 2
    assert ledger.get_transactions()[1].desc == "Second"

def test_balance(ledger):
    ledger.add_transaction("Income", 100, "Cash", "Revenue")
    ledger.add_transaction("Expense", 30, "Food", "Cash")
    bal = ledger.get_balance()
    assert bal["Cash"] == 70   # 100 - 30
    assert bal["Revenue"] == -100
    assert bal["Food"] == 30

def test_search(ledger):
    ledger.add_transaction("Coffee", 3.5, "Food", "Cash", comment="morning", date="2025-01-01 09:00:00")
    ledger.add_transaction("Lunch", 12, "Food", "Cash", date="2025-01-02 12:00:00")
    results = ledger.search(keyword="coffee")
    assert len(results) == 1
    results = ledger.search(min_amount=10)
    assert len(results) == 1
    results = ledger.search(account="food")
    assert len(results) == 2
    results = ledger.search(from_date="2025-01-02 00:00:00")
    assert len(results) == 1
    assert results[0].desc == "Lunch"