import os
import sys
import tempfile
import pytest
import importlib
from pathlib import Path

# Ensure the parent directory is on sys.path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

@pytest.fixture
def temp_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("LEDGER_DATA_DIR", tmpdir)
        yield tmpdir

@pytest.fixture
def ledger(temp_dir):
    import ledger as ledger_module
    importlib.reload(ledger_module)
    return ledger_module.Ledger()

@pytest.fixture
def macro_manager(temp_dir):
    import ledger as ledger_module
    importlib.reload(ledger_module)
    return ledger_module.MacroManager()

@pytest.fixture
def budget_manager(ledger, temp_dir):
    import ledger as ledger_module
    # ledger already reloaded, MacroManager and BudgetManager use the same module
    return ledger_module.BudgetManager(ledger)