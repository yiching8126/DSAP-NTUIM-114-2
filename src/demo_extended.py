#!/usr/bin/env python3
"""
Extended automated demonstration of Ledgerlogic 2.0
Includes typo detection, budgets, macros, undo/redo, and export.
"""

import subprocess
import sys
import time

def run(cmd_args):
    """Run a single ledger command and print output."""
    print(f"\n{'='*70}")
    print(f"> ledger {' '.join(cmd_args)}")
    print('-'*70)
    result = subprocess.run(
        [sys.executable, "ledger.py"] + cmd_args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    time.sleep(0.8)  # pause for readability

def demo():
    print("LedgerLogic 2.0 – Extended Feature Demonstration")
    print("================================================\n")

    # 1. Basic transactions
    print("1. Adding transactions")
    run(["add", "--desc", "Morning Coffee", "--amount", "3.5", "--dr", "Food", "--cr", "Cash"])
    run(["add", "--desc", "Lunch", "--amount", "12", "--dr", "Food", "--cr", "Cash"])
    run(["add", "--desc", "Bus Ticket", "--amount", "1.5", "--dr", "Transport", "--cr", "EasyCard"])
    run(["add", "--desc", "Freelance Payment", "--amount", "250", "--dr", "Cash", "--cr", "Income"])

    # 2. List and balance
    print("\n2. Listing all transactions")
    run(["list"])

    print("\n3. Account balances")
    run(["balance"])

    # 3. Typo detection (one-shot mode)
    print("\n4. Typo detection – mistyping 'add' as 'ad'")
    run(["ad", "--desc", "Should fail", "--amount", "10", "--dr", "A", "--cr", "B"])

    # 4. Budget
    print("\n5. Setting monthly budget for Food ($100)")
    run(["budget", "set", "Food", "100", "--period", "monthly"])

    print("\n6. Budget report")
    run(["budget", "show"])

    # 5. Macros
    print("\n7. Creating a macro 'uber'")
    run(["macro", "add", "uber", "--dr", "Transport", "--cr", "Cash"])

    print("\n8. Listing macros")
    run(["macro", "list"])

    print("\n9. Running macro 'uber' with amount 15.50")
    run(["macro", "run", "uber", "15.50"])

    # 6. Undo/Redo
    print("\n10. Undo last transaction (macro run)")
    run(["undo"])

    print("\n11. List after undo – macro transaction should be gone")
    run(["list"])

    print("\n12. Redo")
    run(["redo"])

    print("\n13. List after redo – macro transaction back")
    run(["list"])

    # 7. Search
    print("\n14. Search for 'Coffee'")
    run(["search", "--keyword", "Coffee"])

    print("\n15. Search for transactions with amount >= 10")
    run(["search", "--min-amount", "10"])

    # 8. Edit and comment
    print("\n16. Edit transaction 1 description to 'Morning Latte'")
    run(["edit", "1", "desc", "Morning Latte"])

    print("\n17. Add comment to transaction 2")
    run(["edit", "2", "comment", "Delicious meal"])

    # 9. Export
    print("\n18. Export all transactions to CSV")
    run(["export", "demo_export.csv"])

    print("\n✅ Demonstration complete. Check 'demo_export.csv' for exported data.")
    print("\nYou can now exit the demo or run additional commands manually.")

if __name__ == "__main__":
    demo()