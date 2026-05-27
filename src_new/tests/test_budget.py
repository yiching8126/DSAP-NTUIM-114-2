import datetime
import pytest
from ledger import BudgetManager

def test_set_budget(budget_manager):
    budget_manager.set_budget("Food", 500, "monthly", "2025-01-01")
    assert len(budget_manager.budgets) == 1
    assert budget_manager.budgets[0].amount == 500

def test_spending_calculation(ledger, budget_manager):
    ledger.add_transaction("Groceries", 100, "Food", "Cash", date="2025-01-15 12:00:00")
    ledger.add_transaction("Restaurant", 50, "Food", "Cash", date="2025-01-20 18:30:00")
    start = "2025-01-01 00:00:00"
    end = "2025-01-31 23:59:59"
    total = budget_manager.get_spending("Food", start, end)
    assert total == 150

def test_budget_report(budget_manager, ledger):
    budget_manager.set_budget("Food", 200, "monthly", "2025-01-01")
    # Use a fixed date for the transaction to ensure it falls in the "current month"
    # We'll mock datetime? Simpler: patch the report's date range.
    # For test reliability, we can add a transaction with today's date.
    ledger.add_transaction("Lunch", 30, "Food", "Cash")
    report = budget_manager.report()
    # There should be one budget entry
    assert len(report) == 1
    assert report[0]["account"] == "Food"
    assert report[0]["actual"] == 30
    assert report[0]["remaining"] == 170