# Ledgerlogic cli, main
import os
import csv
import json
import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import tracemalloc
import copy

console = Console()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# All data files will be stored in the same folder as the script
DATA_FILE = os.path.join(SCRIPT_DIR, "ledger_dict.json")
BUDGET_FILE = os.path.join(SCRIPT_DIR, "budget.json")

# ------------------------------------------------------------
# Undo/Redo stack (global)
# ------------------------------------------------------------
undo_stack = []
redo_stack = []
MAX_UNDO = 20

def save_state(transactions_dict):
    global undo_stack, redo_stack
    copy_state = copy.deepcopy(transactions_dict)
    undo_stack.append(copy_state)
    if len(undo_stack) > MAX_UNDO:
        undo_stack.pop(0)
    redo_stack.clear()

def undo(transactions_dict):
    global undo_stack, redo_stack
    if not undo_stack:
        console.print("[yellow]Nothing to undo.[/yellow]")
        return transactions_dict
    redo_stack.append(copy.deepcopy(transactions_dict))
    transactions_dict = undo_stack.pop()
    save_transactions(transactions_dict)
    console.print("[green]Undo successful.[/green]")
    return transactions_dict

def redo(transactions_dict):
    global undo_stack, redo_stack
    if not redo_stack:
        console.print("[yellow]Nothing to redo.[/yellow]")
        return transactions_dict
    undo_stack.append(copy.deepcopy(transactions_dict))
    transactions_dict = redo_stack.pop()
    save_transactions(transactions_dict)
    console.print("[green]Redo successful.[/green]")
    return transactions_dict

# ------------------------------------------------------------
# Data management
# ------------------------------------------------------------
def load_transactions():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {t["id"]: t for t in data}
            converted = {}
            for key, tx in data.items():
                converted[int(key)] = tx
                if "comment" not in tx:
                    tx["comment"] = ""
            return converted
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
# Core transaction functions
# ------------------------------------------------------------
def add_transaction(transactions_dict, description, amount, debit_acc, credit_acc, comment=""):
    save_state(transactions_dict)
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
# List, balance, search (read-only)
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
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spending = {}
    for tx in transactions_dict.values():
        tx_date = datetime.strptime(tx["date"], "%Y-%m-%d %H:%M:%S")
        if tx_date >= start_of_month:
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
    total_budget = sum(b["amount"] for b in budgets.values())
    total_actual = sum(spending.get(acc, 0) for acc in budgets.keys())
    total_remaining = total_budget - total_actual
    console.print(Panel(f"Total Budget: ${total_budget:.2f} | Total Actual: ${total_actual:.2f} | Remaining: ${total_remaining:.2f}",
                        title="Summary", style="bold"))

# ------------------------------------------------------------
# Import / Export
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
    script_path = os.path.join(SCRIPT_DIR, filename)
    abs_path = filename if os.path.isabs(filename) else None
    if os.path.exists(script_path):
        full_path = script_path
    elif abs_path and os.path.exists(abs_path):
        full_path = abs_path
    else:
        console.print(f"[red]File '{filename}' not found in script folder nor as absolute path.[/red]")
        while True:
            retry = input("Please enter a valid file path (or 'cancel' to abort): ").strip()
            if retry.lower() == "cancel":
                console.print("[yellow]Import cancelled.[/yellow]")
                return transactions_dict
            if os.path.exists(retry):
                full_path = retry
                break
            else:
                console.print(f"[red]Path '{retry}' does not exist. Try again.[/red]")
    ext = os.path.splitext(full_path)[1].lower()
    try:
        if ext == ".json":
            with open(full_path, "r") as f:
                imported = json.load(f)
        elif ext == ".csv":
            imported = []
            with open(full_path, "r", newline="") as f:
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
        save_state(transactions_dict)
        if replace:
            new_dict = {}
            for tx in imported:
                if "comment" not in tx:
                    tx["comment"] = ""
                new_dict[tx["id"]] = tx
            console.print(f"[yellow]Replaced all transactions with {len(imported)} from {full_path}[/yellow]")
            transactions_dict = new_dict
        else:
            max_id = max(transactions_dict.keys(), default=0)
            for tx in imported:
                max_id += 1
                tx["id"] = max_id
                if "comment" not in tx:
                    tx["comment"] = ""
                transactions_dict[max_id] = tx
            console.print(f"[yellow]Merged {len(imported)} transactions from {full_path}[/yellow]")
        save_transactions(transactions_dict)
        console.print("[green]Import successful![/green]")
        return transactions_dict
    except Exception as e:
        console.print(f"[red]Import failed: {e}[/red]")
        return transactions_dict

# ------------------------------------------------------------
# Performance test
# ------------------------------------------------------------

def gen_transactions(n=10000):
    accounts = ["Cash", "Food", "Transport", "Income", "Rent", "Utilities"]
    descriptions = ["Coffee", "Lunch", "Bus", "Salary", "Groceries", "Movie"]
    start_date = datetime(2025, 1, 1)
    transactions = []
    for i in range(1, n+1):
        rand_days = random.randint(0, 365)
        date = start_date + timedelta(days=rand_days)
        # 隨機決定借貸帳戶 (簡單模擬)
        dr = random.choice(accounts)
        cr = random.choice([a for a in accounts if a != dr])
        amount = round(random.uniform(5, 500), 2)
        transactions.append({
            "id": i,
            "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "desc": random.choice(descriptions),
            "amount": amount,
            "dr": dr,
            "cr": cr
        })
    return transactions


def perf_test_list_vs_dict():
    import time
    
    
    file_path = os.path.join(SCRIPT_DIR, 'test_data.json')
    
    # If test data doesn't exist, generate it automatically
    if not os.path.exists(file_path):
        console.print("[yellow]test_data.json not found. Generating 10,000 test transactions...[/yellow]")
        test_data = gen_transactions(10000)
        with open(file_path, "w") as f:
            json.dump(test_data, f, indent=2)
        console.print("[green]Generated test_data.json[/green]")
    else:
        try:
            with open(file_path, "r") as f:
                test_data = json.load(f)
        except:
            console.print("[red]Failed to load test_data.json. Regenerating...[/red]")
            test_data = gen_transactions(10000)
            with open(file_path, "w") as f:
                json.dump(test_data, f, indent=2)
    
    # ... rest of the performance test remains the same ...
    tx_list = test_data.copy()
    tracemalloc.start()
    start = time.time()
    for _ in range(1000):
        target_id = random.randint(1, len(tx_list))
        found = next((t for t in tx_list if t["id"] == target_id), None)
    t_list_search = time.time() - start
    _, peak_list_search = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_list_search_kb = peak_list_search / 1024
    
    tracemalloc.start()
    start = time.time()
    ids_to_delete = set(range(1, 501))
    new_list = [t for t in tx_list if t["id"] not in ids_to_delete]
    for i, t in enumerate(new_list, 1):
        t["id"] = i
    t_list_delete = time.time() - start
    _, peak_list_del = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_list_del_kb = peak_list_del / 1024
    
    tx_dict = {t["id"]: t for t in test_data}
    tracemalloc.start()
    start = time.time()
    for _ in range(1000):
        target_id = random.randint(1, len(tx_dict))
        found = tx_dict.get(target_id)
    t_dict_search = time.time() - start
    _, peak_dict_search = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_dict_search_kb = peak_dict_search / 1024
    
    tracemalloc.start()
    start = time.time()
    for tid in range(1, 501):
        tx_dict.pop(tid, None)
    sorted_items = sorted(tx_dict.items(), key=lambda x: x[0])
    new_dict = {}
    for new_id, (old_id, t) in enumerate(sorted_items, 1):
        t["id"] = new_id
        new_dict[new_id] = t
    t_dict_delete = time.time() - start
    _, peak_dict_del = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_dict_del_kb = peak_dict_del / 1024
    
    table = Table(title="Performance Comparison (List vs Dict)")
    table.add_column("Operation", style="cyan")
    table.add_column("List (sec)", justify="right")
    table.add_column("Dict (sec)", justify="right")
    table.add_column("Speedup", justify="right")
    table.add_column("List Peak Mem (KB)", justify="right")
    table.add_column("Dict Peak Mem (KB)", justify="right")
    table.add_row("1000 random searches", f"{t_list_search:.4f}", f"{t_dict_search:.4f}",
                  f"{t_list_search/t_dict_search:.2f}x", f"{mem_list_search_kb:.2f}", f"{mem_dict_search_kb:.2f}")
    table.add_row("Delete 500 items + reindex", f"{t_list_delete:.4f}", f"{t_dict_delete:.4f}",
                  f"{t_list_delete/t_dict_delete:.2f}x", f"{mem_list_del_kb:.2f}", f"{mem_dict_del_kb:.2f}")
    console.print(table)

# ------------------------------------------------------------
# Help screen
# ------------------------------------------------------------
def show_help():
    help_text = """
    [bold cyan]FULL FEATURE LEDGER - Undo/Redo, Budget, Macros[/bold cyan]

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

    [bold]BUDGET TRACKING[/bold]
    [yellow]budget set <account> <amount>[/yellow] : Set monthly budget
    [yellow]budget show[/yellow]        : Show budget vs actual spending this month

    [bold]UTILITIES[/bold]
    [yellow]search [keyword][/yellow]  : Quick keyword search, or interactive filter
    [yellow]export <file>[/yellow]     : Save to JSON/CSV
    [yellow]import <file>[/yellow]     : Merge from JSON/CSV
    [yellow]import --replace <file>[/yellow] : Replace current data
    [yellow]perftest[/yellow]        : Compare list vs dict performance
    [yellow]help[/yellow]              : This menu
    [yellow]exit[/yellow]              : Quit (auto-save)

    [italic]Examples:[/italic]
      edit 3 amount 49.99
      budget set Food 500
      budget show
    """
    console.print(Panel(help_text, title="Ledger Help", expand=False))

# ------------------------------------------------------------
# Main event loop
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
            elif cmd == "undo":
                transactions = undo(transactions)
            elif cmd == "redo":
                transactions = redo(transactions)
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
