import subprocess
import sys
import time

def run(cmd_args):
    """Run a single ledger command and print output."""
    print(f"\n{'='*60}")
    print(f"> ledger {' '.join(cmd_args)}")
    print('-'*60)
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
    time.sleep(0.5)  # slight pause for readability

# Demo sequence
print("LedgerLogic 2.0 – Automated Demonstration")
print("=========================================")

run(["add", "--desc", "Morning Coffee", "--amount", "3.5", "--dr", "Food", "--cr", "Cash"])
run(["add", "--desc", "Lunch", "--amount", "12", "--dr", "Food", "--cr", "Cash"])
run(["add", "--desc", "Bus Ticket", "--amount", "1.5", "--dr", "Transport", "--cr", "EasyCard"])

print("\n📋 Listing all transactions:")
run(["list"])

print("\n💰 Account balances:")
run(["balance"])

print("\n🎯 Set budget for Food ($100 monthly):")
run(["budget", "set", "Food", "100", "--period", "monthly"])

print("\n📊 Budget report:")
run(["budget", "show"])

print("\n↩️ Undo last transaction (Bus Ticket):")
run(["undo"])

print("\n📋 List after undo:")
run(["list"])

print("\n➡️ Redo:")
run(["redo"])

print("\n📋 List after redo:")
run(["list"])

print("\n🔍 Search transactions containing 'Coffee':")
run(["search", "--keyword", "Coffee"])

print("\n💾 Export to CSV:")
run(["export", "demo_export.csv"])

print("\n✅ Demonstration complete.")