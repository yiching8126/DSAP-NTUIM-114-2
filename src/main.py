# ACC_v1_0.py - Full featured accounting CLI
import json
import os
import csv
import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
DATA_FILE = "ledger_dict.json"
RECUR_FILE = "recurring.json"
BUDGET_FILE = "budget.json"

# ------------------------------------------------------------
# Undo/Redo stack (global)
# ------------------------------------------------------------
undo_stack = []
redo_stack = []
MAX_UNDO = 20

def save_state(transactions_dict):
    """Push current state onto undo stack, clear redo stack."""
    global undo_stack, redo_stack
    # Deep copy (serialize/deserialize to avoid reference issues)
    copy = json.loads(json.dumps(transactions_dict))
    undo_stack.append(copy)
    if len(undo_stack) > MAX_UNDO:
        undo_stack.pop(0)
    redo_stack.clear()

def undo(transactions_dict):
    global undo_stack, redo_stack
    if not undo_stack:
        console.print("[yellow]Nothing to undo.[/yellow]")
        return transactions_dict
    # Save current to redo stack
    redo_stack.append(json.loads(json.dumps(transactions_dict)))
    transactions_dict = undo_stack.pop()
    save_transactions(transactions_dict)
    console.print("[green]Undo successful.[/green]")
    return transactions_dict

def redo(transactions_dict):
    global undo_stack, redo_stack
    if not redo_stack:
        console.print("[yellow]Nothing to redo.[/yellow]")
        return transactions_dict
    # Save current to undo stack
    undo_stack.append(json.loads(json.dumps(transactions_dict)))
    transactions_dict = redo_stack.pop()
    save_transactions(transactions_dict)
    console.print("[green]Redo successful.[/green]")
    return transactions_dict

# ------------------------------------------------------------
# Data management (dict version)
# ------------------------------------------------------------
def load_transactions():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {t["id"]: t for t in data}
            for tx in data.values():
                if "comment" not in tx:
                    tx["comment"] = ""
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_transactions(transactions_dict):
    with open(DATA_FILE, "w") as f:
        json.dump(transactions_dict, f, indent=4)

def rebuild_ids(transactions_dict):
    if not transactions_dict:
        return {}
    sorted_items = sorted(transactions_dict.items(), key=lambda x: x[0])
    new_dict = {}
    for new_id, (old_id, tx) in enumerate(sorted_items, start=1):
        tx["id"] = new_id
        new_dict[new_id] = tx
    return new_dict

# ------------------------------------------------------------
# Core functions (save state before modifications)
# ------------------------------------------------------------
def add_transaction(transactions_dict, description, amount, debit_acc, credit_acc, comment=""):
    save_state(transactions_dict)   # for undo
    new_id = max(transactions_dict.keys(), default=0) + 1
    entry = {
        "id": new_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "desc": description,
        "amount": float(amount),
        "dr": debit_acc,
        "cr": credit_acc,
        "comment": comment
    }
    transactions_dict[new_id] = entry
    save_transactions(transactions_dict)
    console.print(f"[green]✔[/green] Added: {description} (${amount})")
    return transactions_dict

def delete_transaction(transactions_dict, tx_id):
    save_state(transactions_dict)
    if tx_id not in transactions_dict:
        console.print(f"[red]ID {tx_id} not found.[/red]")
        return transactions_dict
    del transactions_dict[tx_id]
    new_dict = rebuild_ids(transactions_dict)
    save_transactions(new_dict)
    console.print(f"[green]Deleted transaction {tx_id}.[/green]")
    return new_dict

def edit_transaction(transactions_dict, tx_id, field, new_value):
    save_state(transactions_dict)
    if tx_id not in transactions_dict:
        console.print(f"[red]ID {tx_id} not found.[/red]")
        return transactions_dict
    field = field.lower()
    tx = transactions_dict[tx_id]
    if field in ["description", "desc"]:
        tx["desc"] = new_value
    elif field == "amount":
        try:
            tx["amount"] = float(new_value)
        except ValueError:
            console.print("[red]Amount must be a number.[/red]")
            return transactions_dict
    elif field in ["dr", "debit"]:
        tx["dr"] = new_value
    elif field in ["cr", "credit"]:
        tx["cr"] = new_value
    elif field == "date":
        tx["date"] = new_value
    elif field == "comment":
        tx["comment"] = new_value
    else:
        console.print("[red]Invalid field. Options: description, amount, dr, cr, date, comment[/red]")
        return transactions_dict
    save_transactions(transactions_dict)
    console.print(f"[green]Updated transaction {tx_id} → {field} = {new_value}[/green]")
    return transactions_dict

def add_comment(transactions_dict, tx_id, comment_text):
    return edit_transaction(transactions_dict, tx_id, "comment", comment_text)

# ------------------------------------------------------------
# List, balance, search (read-only, no state save)
# ------------------------------------------------------------
def list_transactions(transactions_dict, sort_key="date"):
    if not transactions_dict:
        console.print("[yellow]No transactions.[/yellow]")
        return
    tx_list = list(transactions_dict.values())
    if sort_key == "amount":
        sorted_tx = sorted(tx_list, key=lambda x: x["amount"])
    else:
        sorted_tx = sorted(tx_list, key=lambda x: x["date"])
    table = Table(title=f"Transactions (sorted by {sort_key})")
    table.add_column("ID", style="dim")
    table.add_column("Date")
    table.add_column("Description")
    table.add_column("Debit (Dr)")
    table.add_column("Credit (Cr)")
    table.add_column("Amount", justify="right", style="bold")
    table.add_column("Comment", style="italic")
    for tx in sorted_tx:
        table.add_row(
            str(tx["id"]), tx["date"], tx["desc"],
            tx["dr"], tx["cr"], f"{tx['amount']:.2f}",
            tx.get("comment", "")[:30]
        )
    console.print(table)

def show_balance(transactions_dict):
    balances = {}
    for tx in transactions_dict.values():
        balances[tx["dr"]] = balances.get(tx["dr"], 0) + tx["amount"]
        balances[tx["cr"]] = balances.get(tx["cr"], 0) - tx["amount"]
    if not balances:
        console.print("[yellow]No transactions to compute balance.[/yellow]")
        return
    table = Table(title="Account Balances")
    table.add_column("Account")
    table.add_column("Balance", justify="right")
    for acc, amt in balances.items():
        color = "green" if amt >= 0 else "red"
        table.add_row(acc, f"[{color}]{amt:.2f}[/{color}]")
    console.print(table)

def search_transactions(transactions_dict, **filters):
    results = []
    for tx in transactions_dict.values():
        match = True
        if "min_amount" in filters and tx["amount"] < filters["min_amount"]:
            match = False
        if "max_amount" in filters and tx["amount"] > filters["max_amount"]:
            match = False
        if "account" in filters:
            acc = filters["account"].lower()
            if tx["dr"].lower() != acc and tx["cr"].lower() != acc:
                match = False
        if "keyword" in filters:
            if filters["keyword"].lower() not in tx["desc"].lower():
                match = False
        if "from_date" in filters and tx["date"] < filters["from_date"]:
            match = False
        if "to_date" in filters and tx["date"] > filters["to_date"]:
            match = False
        if match:
            results.append(tx)
    if not results:
        console.print("[yellow]No matching transactions.[/yellow]")
        return
    table = Table(title="Search Results")
    table.add_column("ID", style="dim")
    table.add_column("Date")
    table.add_column("Description")
    table.add_column("Debit (Dr)")
    table.add_column("Credit (Cr)")
    table.add_column("Amount", justify="right")
    for tx in results:
        table.add_row(
            str(tx["id"]), tx["date"], tx["desc"],
            tx["dr"], tx["cr"], f"{tx['amount']:.2f}"
        )
    console.print(table)

# ------------------------------------------------------------
# Macros
# ------------------------------------------------------------
MACROS = {
    "lunch": {"dr": "Food", "cr": "Cash"},
    "bus": {"dr": "Transport", "cr": "EasyCard"},
    "misc": {"dr": "Miscellaneous", "cr": "Cash"}
}

def run_macro(transactions_dict, name, amount):
    if name not in MACROS:
        console.print(f"[red]Macro '{name}' not found. Available: {', '.join(MACROS.keys())}[/red]")
        return transactions_dict
    m = MACROS[name]
    return add_transaction(transactions_dict, f"Macro: {name}", amount, m["dr"], m["cr"])

# ------------------------------------------------------------
# Recurring Transactions
# ------------------------------------------------------------
def load_recurring():
    if not os.path.exists(RECUR_FILE):
        return []
    try:
        with open(RECUR_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_recurring(recur_list):
    with open(RECUR_FILE, "w") as f:
        json.dump(recur_list, f, indent=4)

def add_recurring(description, amount, debit_acc, credit_acc, interval_days, next_date=None):
    recur_list = load_recurring()
    if next_date is None:
        next_date = datetime.now().strftime("%Y-%m-%d")
    new_id = max([r.get("id", 0) for r in recur_list], default=0) + 1
    entry = {
        "id": new_id,
        "desc": description,
        "amount": float(amount),
        "dr": debit_acc,
        "cr": credit_acc,
        "interval_days": interval_days,
        "next_due": next_date
    }
    recur_list.append(entry)
    save_recurring(recur_list)
    console.print(f"[green]Recurring rule added: {description} every {interval_days} days[/green]")

def list_recurring():
    recur_list = load_recurring()
    if not recur_list:
        console.print("[yellow]No recurring rules.[/yellow]")
        return
    table = Table(title="Recurring Transactions")
    table.add_column("ID", style="dim")
    table.add_column("Description")
    table.add_column("Amount")
    table.add_column("Debit")
    table.add_column("Credit")
    table.add_column("Interval (days)")
    table.add_column("Next due")
    for r in recur_list:
        table.add_row(
            str(r["id"]), r["desc"], f"{r['amount']:.2f}",
            r["dr"], r["cr"], str(r["interval_days"]), r["next_due"]
        )
    console.print(table)

def delete_recurring(rule_id):
    recur_list = load_recurring()
    new_list = [r for r in recur_list if r.get("id") != rule_id]
    if len(new_list) == len(recur_list):
        console.print(f"[red]Rule ID {rule_id} not found.[/red]")
        return
    save_recurring(new_list)
    console.print(f"[green]Deleted recurring rule {rule_id}.[/green]")

def run_recurring(transactions_dict):
    """Check all recurring rules and add transactions that are due."""
    recur_list = load_recurring()
    today = datetime.now().date()
    added_count = 0
    for rule in recur_list:
        due_date = datetime.strptime(rule["next_due"], "%Y-%m-%d").date()
        if due_date <= today:
            # Add transaction
            transactions_dict = add_transaction(
                transactions_dict,
                f"Recurring: {rule['desc']}",
                rule["amount"],
                rule["dr"],
                rule["cr"],
                comment=f"Auto from recurring rule ID {rule['id']}"
            )
            added_count += 1
            # Update next due date
            next_due = due_date + timedelta(days=rule["interval_days"])
            rule["next_due"] = next_due.strftime("%Y-%m-%d")
    if added_count > 0:
        save_recurring(recur_list)
        console.print(f"[green]Added {added_count} recurring transaction(s).[/green]")
    else:
        console.print("[yellow]No recurring transactions due today.[/yellow]")
    return transactions_dict

# ------------------------------------------------------------
# Budget Tracking
# ------------------------------------------------------------
def load_budgets():
    if not os.path.exists(BUDGET_FILE):
        return {}
    try:
        with open(BUDGET_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_budgets(budgets):
    with open(BUDGET_FILE, "w") as f:
        json.dump(budgets, f, indent=4)

def set_budget(account, amount, period="monthly"):
    budgets = load_budgets()
    budgets[account] = {"amount": float(amount), "period": period}
    save_budgets(budgets)
    console.print(f"[green]Budget for {account}: ${amount} ({period})[/green]")

def show_budget_report(transactions_dict):
    budgets = load_budgets()
    if not budgets:
        console.print("[yellow]No budgets set. Use 'budget set <account> <amount>'[/yellow]")
        return
    # Calculate current period spending (this month by default)
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spending = {}
    for tx in transactions_dict.values():
        tx_date = datetime.strptime(tx["date"], "%Y-%m-%d %H:%M:%S")
        if tx_date >= start_of_month:
            # Only debit accounts (expenses) count toward budget
            acc = tx["dr"]
            if acc in budgets:
                spending[acc] = spending.get(acc, 0) + tx["amount"]
    table = Table(title="Budget vs Actual (This Month)")
    table.add_column("Account")
    table.add_column("Budget", justify="right")
    table.add_column("Actual", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Status", justify="center")
    for acc, budget_info in budgets.items():
        budget_amt = budget_info["amount"]
        actual = spending.get(acc, 0)
        remaining = budget_amt - actual
        status = "✅ On track" if remaining >= 0 else "⚠️ Over budget"
        color = "green" if remaining >= 0 else "red"
        table.add_row(acc, f"${budget_amt:.2f}", f"${actual:.2f}",
                      f"[{color}]${remaining:.2f}[/{color}]", status)
    console.print(table)
    # Also show totals
    total_budget = sum(b["amount"] for b in budgets.values())
    total_actual = sum(spending.get(acc, 0) for acc in budgets.keys())
    total_remaining = total_budget - total_actual
    console.print(Panel(f"Total Budget: ${total_budget:.2f} | Total Actual: ${total_actual:.2f} | Remaining: ${total_remaining:.2f}",
                        title="Summary", style="bold"))

# ------------------------------------------------------------
# Import / Export (unchanged)
# ------------------------------------------------------------
def export_transactions(transactions_dict, filename):
    tx_list = list(transactions_dict.values())
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == ".json":
            with open(filename, "w") as f:
                json.dump(tx_list, f, indent=4)
            console.print(f"[green]Exported {len(tx_list)} transactions to {filename}[/green]")
        elif ext == ".csv":
            with open(filename, "w", newline="") as f:
                if not tx_list:
                    writer = csv.writer(f)
                    writer.writerow(["id", "date", "desc", "amount", "dr", "cr", "comment"])
                else:
                    writer = csv.DictWriter(f, fieldnames=["id", "date", "desc", "amount", "dr", "cr", "comment"])
                    writer.writeheader()
                    writer.writerows(tx_list)
            console.print(f"[green]Exported {len(tx_list)} transactions to {filename}[/green]")
        else:
            console.print("[red]Unsupported format. Use .json or .csv[/red]")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")

def import_transactions(transactions_dict, filename, replace=False):
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == ".json":
            with open(filename, "r") as f:
                imported = json.load(f)
        elif ext == ".csv":
            imported = []
            with open(filename, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["id"] = int(row["id"])
                    row["amount"] = float(row["amount"])
                    if "comment" not in row:
                        row["comment"] = ""
                    imported.append(row)
        else:
            console.print("[red]Unsupported format. Use .json or .csv[/red]")
            return transactions_dict
        if not isinstance(imported, list):
            console.print("[red]Invalid file: root must be a list of transactions[/red]")
            return transactions_dict
        save_state(transactions_dict)   # for undo
        if replace:
            new_dict = {}
            for tx in imported:
                if "comment" not in tx:
                    tx["comment"] = ""
                new_dict[tx["id"]] = tx
            console.print(f"[yellow]Replaced all transactions with {len(imported)} from {filename}[/yellow]")
            transactions_dict = new_dict
        else:
            max_id = max(transactions_dict.keys(), default=0)
            for tx in imported:
                max_id += 1
                tx["id"] = max_id
                if "comment" not in tx:
                    tx["comment"] = ""
                transactions_dict[max_id] = tx
            console.print(f"[yellow]Merged {len(imported)} transactions from {filename}[/yellow]")
        save_transactions(transactions_dict)
        console.print("[green]Import successful![/green]")
        return transactions_dict
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")
        return transactions_dict

# ------------------------------------------------------------
# Performance test
# ------------------------------------------------------------
def perf_test_list_vs_dict():
    try:
        with open("test_data.json", "r") as f:
            test_data = json.load(f)
    except FileNotFoundError:
        console.print("[red]Please run generate_test_data.py first[/red]")
        return
    import time
    tx_list = test_data.copy()
    start = time.time()
    for _ in range(1000):
        target_id = random.randint(1, len(tx_list))
        found = next((t for t in tx_list if t["id"] == target_id), None)
    t_list_search = time.time() - start
    start = time.time()
    ids_to_delete = set(range(1, 501))
    new_list = [t for t in tx_list if t["id"] not in ids_to_delete]
    for i, t in enumerate(new_list, 1):
        t["id"] = i
    t_list_delete = time.time() - start
    tx_dict = {t["id"]: t for t in test_data}
    start = time.time()
    for _ in range(1000):
        target_id = random.randint(1, len(tx_dict))
        found = tx_dict.get(target_id)
    t_dict_search = time.time() - start
    start = time.time()
    for tid in range(1, 501):
        tx_dict.pop(tid, None)
    sorted_items = sorted(tx_dict.items(), key=lambda x: x[0])
    new_dict = {}
    for new_id, (old_id, t) in enumerate(sorted_items, 1):
        t["id"] = new_id
        new_dict[new_id] = t
    t_dict_delete = time.time() - start
    table = Table(title="Performance Comparison (List vs Dict)")
    table.add_column("Operation", style="cyan")
    table.add_column("List (seconds)", justify="right")
    table.add_column("Dict (seconds)", justify="right")
    table.add_column("Speedup", justify="right")
    table.add_row("1000 random searches", f"{t_list_search:.4f}", f"{t_dict_search:.4f}", f"{t_list_search/t_dict_search:.2f}x")
    table.add_row("Delete 500 items + reindex", f"{t_list_delete:.4f}", f"{t_dict_delete:.4f}", f"{t_list_delete/t_dict_delete:.2f}x")
    console.print(table)

# ------------------------------------------------------------
# Help screen (updated with all new commands)
# ------------------------------------------------------------
def show_help():
    help_text = """
    [bold cyan]FULL FEATURE LEDGER - Undo/Redo, Recurring, Budget[/bold cyan]

    [bold]TRANSACTIONS[/bold]
    [yellow]add[/yellow]               : Add transaction (interactive)
    [yellow]misc <amount>[/yellow]    : Quick misc expense
    [yellow]macro <name> <amt>[/yellow] : Use macro (lunch, bus, misc)
    [yellow]list [date|amount][/yellow] : Show all transactions
    [yellow]balance[/yellow]           : Account balances
    [yellow]delete <id>[/yellow]       : Remove transaction
    [yellow]edit <id> <field> <new>[/yellow] : Modify (desc, amount, dr, cr, date, comment)
    [yellow]comment <id> <text>[/yellow] : Add/edit comment

    [bold]UNDO/REDO[/bold]
    [yellow]undo[/yellow]               : Revert last change
    [yellow]redo[/yellow]               : Restore undone change

    [bold]RECURRING TRANSACTIONS[/bold]
    [yellow]recur add <desc> <amt> <dr> <cr> <interval_days>[/yellow] : Create recurring rule
    [yellow]recur list[/yellow]         : Show recurring rules
    [yellow]recur delete <id>[/yellow]  : Remove a rule
    [yellow]recur run[/yellow]          : Add all due recurring transactions

    [bold]BUDGET TRACKING[/bold]
    [yellow]budget set <account> <amount>[/yellow] : Set monthly budget
    [yellow]budget show[/yellow]        : Show budget vs actual spending this month

    [bold]UTILITIES[/bold]
    [yellow]search [keyword][/yellow]  : Quick keyword search, or interactive filter
    [yellow]export <file>[/yellow]     : Save to JSON/CSV
    [yellow]import <file>[/yellow]     : Merge from JSON/CSV
    [yellow]import --replace <file>[/yellow] : Replace current data
    [yellow]perftest[/yellow]          : Compare list vs dict performance
    [yellow]help[/yellow]              : This menu
    [yellow]exit[/yellow]              : Quit (auto-save)

    [italic]Examples:[/italic]
      edit 3 amount 49.99
      recur add "Rent" 1500 Rent Cash 30
      recur run
      budget set Food 500
      budget show
    """
    console.print(Panel(help_text, title="Ledger Help", expand=False))

# ------------------------------------------------------------
# Main event loop (with new commands)
# ------------------------------------------------------------
def main():
    transactions = load_transactions()
    console.print("[bold green]Full Feature Ledger[/bold green] - Type [yellow]help[/yellow] for all commands")

    while True:
        try:
            raw = input("\n>> ").strip()
            if not raw:
                continue
            parts = raw.split()
            cmd = parts[0].lower()

            if cmd == "exit":
                save_transactions(transactions)
                console.print("[bold]Goodbye![/bold]")
                break

            elif cmd == "help":
                show_help()

            # === Undo/Redo ===
            elif cmd == "undo":
                transactions = undo(transactions)
            elif cmd == "redo":
                transactions = redo(transactions)

            # === Transactions ===
            elif cmd == "add":
                desc = input("Description: ")
                amt = float(input("Amount: "))
                dr = input("Debit account: ")
                cr = input("Credit account: ")
                comment = input("Comment (optional): ")
                transactions = add_transaction(transactions, desc, amt, dr, cr, comment)

            elif cmd == "misc":
                if len(parts) != 2:
                    console.print("[red]Usage: misc <amount>[/red]")
                    continue
                try:
                    amt = float(parts[1])
                except ValueError:
                    console.print("[red]Amount must be a number.[/red]")
                    continue
                transactions = run_macro(transactions, "misc", amt)

            elif cmd == "macro":
                if len(parts) < 3:
                    console.print("[red]Usage: macro <name> <amount>[/red]")
                    continue
                name = parts[1].lower()
                try:
                    amt = float(parts[2])
                except ValueError:
                    console.print("[red]Amount must be a number.[/red]")
                    continue
                transactions = run_macro(transactions, name, amt)

            elif cmd == "list":
                sort_by = "date"
                if len(parts) > 1 and parts[1].lower() in ["amount", "date"]:
                    sort_by = parts[1].lower()
                list_transactions(transactions, sort_key=sort_by)

            elif cmd == "balance":
                show_balance(transactions)

            elif cmd == "delete":
                if len(parts) != 2:
                    console.print("[red]Usage: delete <id>[/red]")
                    continue
                try:
                    tx_id = int(parts[1])
                except ValueError:
                    console.print("[red]ID must be a number.[/red]")
                    continue
                transactions = delete_transaction(transactions, tx_id)

            elif cmd == "edit":
                if len(parts) < 4:
                    console.print("[red]Usage: edit <id> <field> <new_value>[/red]")
                    console.print("[yellow]Fields: description, amount, dr, cr, date, comment[/yellow]")
                    continue
                try:
                    tx_id = int(parts[1])
                except ValueError:
                    console.print("[red]ID must be a number.[/red]")
                    continue
                field = parts[2]
                new_value = " ".join(parts[3:])
                transactions = edit_transaction(transactions, tx_id, field, new_value)

            elif cmd == "comment":
                if len(parts) < 3:
                    console.print("[red]Usage: comment <id> <your comment ...>[/red]")
                    continue
                try:
                    tx_id = int(parts[1])
                except ValueError:
                    console.print("[red]ID must be a number.[/red]")
                    continue
                comment_text = " ".join(parts[2:])
                transactions = add_comment(transactions, tx_id, comment_text)

            # === Recurring ===
            elif cmd == "recur":
                if len(parts) < 2:
                    console.print("[red]Usage: recur add/list/delete/run[/red]")
                    continue
                sub = parts[1].lower()
                if sub == "add":
                    if len(parts) < 7:
                        console.print("[red]Usage: recur add <desc> <amount> <dr> <cr> <interval_days>[/red]")
                        continue
                    desc = parts[2]
                    try:
                        amt = float(parts[3])
                        interval = int(parts[6])
                    except ValueError:
                        console.print("[red]Amount and interval must be numbers.[/red]")
                        continue
                    dr = parts[4]
                    cr = parts[5]
                    add_recurring(desc, amt, dr, cr, interval)
                elif sub == "list":
                    list_recurring()
                elif sub == "delete":
                    if len(parts) != 3:
                        console.print("[red]Usage: recur delete <id>[/red]")
                        continue
                    try:
                        rid = int(parts[2])
                    except ValueError:
                        console.print("[red]ID must be a number.[/red]")
                        continue
                    delete_recurring(rid)
                elif sub == "run":
                    transactions = run_recurring(transactions)
                else:
                    console.print("[red]Unknown recur subcommand.[/red]")

            # === Budget ===
            elif cmd == "budget":
                if len(parts) < 2:
                    console.print("[red]Usage: budget set <account> <amount>  or  budget show[/red]")
                    continue
                sub = parts[1].lower()
                if sub == "set":
                    if len(parts) != 4:
                        console.print("[red]Usage: budget set <account> <amount>[/red]")
                        continue
                    account = parts[2]
                    try:
                        amt = float(parts[3])
                    except ValueError:
                        console.print("[red]Amount must be a number.[/red]")
                        continue
                    set_budget(account, amt)
                elif sub == "show":
                    show_budget_report(transactions)
                else:
                    console.print("[red]Unknown budget subcommand.[/red]")

            # === Search ===
            elif cmd == "search" and len(parts) > 1:
                keyword = " ".join(parts[1:])
                search_transactions(transactions, keyword=keyword)
            elif cmd == "search":
                console.print("[cyan]Search filters (empty to skip):[/cyan]")
                min_amt = input("Min amount (optional): ")
                max_amt = input("Max amount (optional): ")
                account = input("Account name (dr or cr, optional): ")
                keyword = input("Keyword in description: ")
                kwargs = {}
                if min_amt.strip():
                    kwargs["min_amount"] = float(min_amt)
                if max_amt.strip():
                    kwargs["max_amount"] = float(max_amt)
                if account.strip():
                    kwargs["account"] = account
                if keyword.strip():
                    kwargs["keyword"] = keyword
                search_transactions(transactions, **kwargs)

            # === Export/Import ===
            elif cmd == "export":
                if len(parts) != 2:
                    console.print("[red]Usage: export <filename.json|csv>[/red]")
                    continue
                export_transactions(transactions, parts[1])
            elif cmd == "import":
                replace = False
                if len(parts) >= 2 and parts[1] == "--replace":
                    replace = True
                    filename = parts[2] if len(parts) > 2 else None
                else:
                    filename = parts[1] if len(parts) > 1 else None
                if not filename:
                    console.print("[red]Usage: import <filename> or import --replace <filename>[/red]")
                    continue
                transactions = import_transactions(transactions, filename, replace=replace)

            # === Performance ===
            elif cmd == "perftest":
                perf_test_list_vs_dict()

            else:
                console.print(f"[red]Unknown command: {cmd}[/red] - try 'help'")

        except KeyboardInterrupt:
            save_transactions(transactions)
            console.print("\n[bold]Interrupted. Exiting.[/bold]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()