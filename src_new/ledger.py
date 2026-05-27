#!/usr/bin/env python3
"""
Ledgerlogic 2.0 - Professional CLI Accounting Tool
Refactored with persistent undo, macros, budgets, reports, interactive mode.
"""

import os
import sys
import json
import csv
import argparse
import shlex
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ----------------------------------------------------------------------
# Path handling: respect LEDGER_DATA_DIR env var for testing
# ----------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_DIR = os.environ.get("LEDGER_DATA_DIR", BASE_DIR)

DATA_FILE = os.path.join(SCRIPT_DIR, "ledger_dict.json")
JOURNAL_FILE = os.path.join(SCRIPT_DIR, "journal.json")
MACRO_FILE = os.path.join(SCRIPT_DIR, "macros.json")
BUDGET_FILE = os.path.join(SCRIPT_DIR, "budget.json")

console = Console()

# ----------------------------------------------------------------------
# Data Models
# ----------------------------------------------------------------------
@dataclass
class Transaction:
    id: int
    date: str
    desc: str
    amount: float
    dr: str
    cr: str
    comment: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(**data)


@dataclass
class Macro:
    name: str
    dr: str
    cr: str


@dataclass
class Budget:
    account: str
    amount: float
    period: str
    start_date: str
    end_date: Optional[str] = None


# ----------------------------------------------------------------------
# Command Pattern for Journal
# ----------------------------------------------------------------------
class Command:
    def apply(self, ledger: "Ledger") -> None:
        raise NotImplementedError

    def undo(self, ledger: "Ledger") -> None:
        raise NotImplementedError

    def to_dict(self) -> dict:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict, ledger: "Ledger") -> "Command":
        cmd_type = data["type"]
        if cmd_type == "add":
            return AddCommand.from_dict(data, ledger)
        elif cmd_type == "edit":
            return EditCommand.from_dict(data, ledger)
        elif cmd_type == "delete":
            return DeleteCommand.from_dict(data, ledger)
        else:
            raise ValueError(f"Unknown command type: {cmd_type}")


class AddCommand(Command):
    def __init__(self, tx: Transaction):
        self.tx = tx

    def apply(self, ledger: "Ledger") -> None:
        new_id = max(ledger._transactions.keys(), default=0) + 1
        self.tx.id = new_id
        ledger._transactions[new_id] = self.tx
        ledger._dirty = True

    def undo(self, ledger: "Ledger") -> None:
        if self.tx.id in ledger._transactions:
            del ledger._transactions[self.tx.id]
            ledger._dirty = True

    def to_dict(self) -> dict:
        return {"type": "add", "tx": self.tx.to_dict()}

    @classmethod
    def from_dict(cls, data: dict, ledger: "Ledger") -> "AddCommand":
        return cls(Transaction.from_dict(data["tx"]))


class EditCommand(Command):
    def __init__(self, tx_id: int, field: str, old_value: Any, new_value: Any):
        self.tx_id = tx_id
        self.field = field
        self.old_value = old_value
        self.new_value = new_value

    def apply(self, ledger: "Ledger") -> None:
        tx = ledger._transactions.get(self.tx_id)
        if tx:
            setattr(tx, self.field, self.new_value)
            ledger._dirty = True

    def undo(self, ledger: "Ledger") -> None:
        tx = ledger._transactions.get(self.tx_id)
        if tx:
            setattr(tx, self.field, self.old_value)
            ledger._dirty = True

    def to_dict(self) -> dict:
        return {
            "type": "edit",
            "tx_id": self.tx_id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }

    @classmethod
    def from_dict(cls, data: dict, ledger: "Ledger") -> "EditCommand":
        return cls(data["tx_id"], data["field"], data["old_value"], data["new_value"])


class DeleteCommand(Command):
    def __init__(self, tx: Transaction):
        self.tx = tx

    def apply(self, ledger: "Ledger") -> None:
        if self.tx.id in ledger._transactions:
            del ledger._transactions[self.tx.id]
            ledger._dirty = True

    def undo(self, ledger: "Ledger") -> None:
        ledger._transactions[self.tx.id] = self.tx
        ledger._dirty = True

    def to_dict(self) -> dict:
        return {"type": "delete", "tx": self.tx.to_dict()}

    @classmethod
    def from_dict(cls, data: dict, ledger: "Ledger") -> "DeleteCommand":
        return cls(Transaction.from_dict(data["tx"]))


# ----------------------------------------------------------------------
# Ledger Core
# ----------------------------------------------------------------------
class Ledger:
    def __init__(self):
        self._transactions: Dict[int, Transaction] = {}
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._dirty = False
        self._load_from_disk()

    def _load_from_disk(self):
        # 1. Clear current state to avoid duplication
        self._transactions = {}
        
        # 2. Load DATA_FILE
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    for tx_dict in data:
                        tx = Transaction.from_dict(tx_dict)
                        self._transactions[tx.id] = tx
            except (json.JSONDecodeError, IOError):
                pass

        # 3. Replay Journal (Crucial: only replay if it exists)
        if os.path.exists(JOURNAL_FILE):
            try:
                with open(JOURNAL_FILE, "r") as f:
                    journal = json.load(f)
                for cmd_dict in journal:
                    # Use a fresh instance of command to apply
                    cmd = Command.from_dict(cmd_dict, self)
                    cmd.apply(self)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Do NOT clear the journal here in the constructor, 
        # as multiple processes might be reading it.

    def _save_checkpoint(self):
        tx_list = [tx.to_dict() for tx in self._transactions.values()]
        with open(DATA_FILE, "w") as f:
            json.dump(tx_list, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        self._clear_journal()
        self._dirty = False

    def _append_to_journal(self, cmd: Command):
        journal = []
        if os.path.exists(JOURNAL_FILE):
            try:
                with open(JOURNAL_FILE, "r") as f:
                    journal = json.load(f)
            except:
                pass
        journal.append(cmd.to_dict())
        if len(journal) > 1000:
            journal = journal[-1000:]
        with open(JOURNAL_FILE, "w") as f:
            json.dump(journal, f, indent=2)
            f.flush()
            os.fsync(f.fileno())   # force write to disk

    def _clear_journal(self):
        if os.path.exists(JOURNAL_FILE):
            os.remove(JOURNAL_FILE)

    def _record_command(self, cmd: Command):
        cmd.apply(self)
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
        self._append_to_journal(cmd)
        
        self._save_checkpoint()

    # ---------- Public API ----------
    def add_transaction(
        self,
        desc: str,
        amount: float,
        dr: str,
        cr: str,
        comment: str = "",
        date: Optional[str] = None,
    ) -> Transaction:
        new_id = max(self._transactions.keys(), default=0) + 1
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tx = Transaction(
            id=new_id,
            date=date,
            desc=desc,
            amount=amount,
            dr=dr,
            cr=cr,
            comment=comment,
        )
        cmd = AddCommand(tx)
        self._record_command(cmd)
        return tx

    def delete_transaction(self, tx_id: int) -> bool:
        tx = self._transactions.get(tx_id)
        if not tx:
            return False
        cmd = DeleteCommand(tx)
        self._record_command(cmd)
        return True

    def edit_transaction(self, tx_id: int, field: str, new_value: Any) -> bool:
        tx = self._transactions.get(tx_id)
        if not tx:
            return False
        old_value = getattr(tx, field)
        if old_value == new_value:
            return True
        cmd = EditCommand(tx_id, field, old_value, new_value)
        self._record_command(cmd)
        return True

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo(self)
        self._redo_stack.append(cmd)
        self._save_checkpoint()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.apply(self)
        self._undo_stack.append(cmd)
        self._save_checkpoint()
        return True

    def get_transactions(self, sort_by: str = "date") -> List[Transaction]:
        tx_list = list(self._transactions.values())
        if sort_by == "amount":
            tx_list.sort(key=lambda x: x.amount)
        else:
            tx_list.sort(key=lambda x: x.date)
        return tx_list

    def get_balance(self, as_of: Optional[str] = None) -> Dict[str, float]:
        balances = {}
        for tx in self._transactions.values():
            if as_of and tx.date > as_of:
                continue
            balances[tx.dr] = balances.get(tx.dr, 0) + tx.amount
            balances[tx.cr] = balances.get(tx.cr, 0) - tx.amount
        return balances

    def search(self, **filters) -> List[Transaction]:
        results = []
        for tx in self._transactions.values():
            match = True
            if "min_amount" in filters and tx.amount < filters["min_amount"]:
                match = False
            if "max_amount" in filters and tx.amount > filters["max_amount"]:
                match = False
            if "account" in filters:
                acc = filters["account"].lower()
                if tx.dr.lower() != acc and tx.cr.lower() != acc:
                    match = False
            if "keyword" in filters:
                kw = filters["keyword"].lower()
                if kw not in tx.desc.lower() and kw not in tx.comment.lower():
                    match = False
            if "from_date" in filters and tx.date < filters["from_date"]:
                match = False
            if "to_date" in filters and tx.date > filters["to_date"]:
                match = False
            if match:
                results.append(tx)
        return results

    def export(self, filename: str, transactions: Optional[List[Transaction]] = None):
        if transactions is None:
            transactions = list(self._transactions.values())
        ext = os.path.splitext(filename)[1].lower()
        data = [tx.to_dict() for tx in transactions]
        if ext == ".json":
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
        elif ext == ".csv":
            with open(filename, "w", newline="") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    f.write("")
        else:
            raise ValueError("Unsupported format. Use .json or .csv")

    def import_transactions(self, filename: str, replace: bool = False):
        ext = os.path.splitext(filename)[1].lower()
        with open(filename, "r") as f:
            if ext == ".json":
                imported_raw = json.load(f)
            elif ext == ".csv":
                reader = csv.DictReader(f)
                imported_raw = list(reader)
            else:
                raise ValueError("Unsupported format")
        imported_txs = []
        for item in imported_raw:
            if "amount" in item:
                item["amount"] = float(item["amount"])
            if "id" in item:
                item["id"] = int(item["id"])
            if "comment" not in item:
                item["comment"] = ""
            imported_txs.append(Transaction.from_dict(item))

        if replace:
            for tx_id in list(self._transactions.keys()):
                self.delete_transaction(tx_id)
            for tx in imported_txs:
                self.add_transaction(tx.desc, tx.amount, tx.dr, tx.cr, tx.comment, tx.date)
        else:
            for tx in imported_txs:
                self.add_transaction(tx.desc, tx.amount, tx.dr, tx.cr, tx.comment, tx.date)

    def rebuild_ids(self):
        sorted_txs = sorted(self._transactions.values(), key=lambda x: x.id)
        new_map = {}
        for new_id, tx in enumerate(sorted_txs, 1):
            tx.id = new_id
            new_map[new_id] = tx
        self._transactions = new_map
        self._save_checkpoint()


# ----------------------------------------------------------------------
# Macros Management
# ----------------------------------------------------------------------
class MacroManager:
    def __init__(self):
        self.macros: Dict[str, Macro] = {}
        self._load()

    def _load(self):
        if os.path.exists(MACRO_FILE):
            try:
                with open(MACRO_FILE, "r") as f:
                    data = json.load(f)
                    for name, m in data.items():
                        self.macros[name] = Macro(name, m["dr"], m["cr"])
            except:
                pass
        if not self.macros:
            self.macros["lunch"] = Macro("lunch", "Food", "Cash")
            self.macros["bus"] = Macro("bus", "Transport", "EasyCard")
            self.macros["misc"] = Macro("misc", "Miscellaneous", "Cash")
            self._save()

    def _save(self):
        data = {name: {"dr": m.dr, "cr": m.cr} for name, m in self.macros.items()}
        with open(MACRO_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def list_macros(self) -> List[Macro]:
        return list(self.macros.values())

    def add_macro(self, name: str, dr: str, cr: str):
        self.macros[name] = Macro(name, dr, cr)
        self._save()

    def remove_macro(self, name: str) -> bool:
        if name in self.macros:
            del self.macros[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> Optional[Macro]:
        return self.macros.get(name)


# ----------------------------------------------------------------------
# Budget Tracking
# ----------------------------------------------------------------------
class BudgetManager:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self.budgets: List[Budget] = []
        self._load()

    def _load(self):
        if os.path.exists(BUDGET_FILE):
            try:
                with open(BUDGET_FILE, "r") as f:
                    data = json.load(f)
                    for b in data:
                        self.budgets.append(Budget(**b))
            except:
                pass

    def _save(self):
        data = [asdict(b) for b in self.budgets]
        with open(BUDGET_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def set_budget(
        self,
        account: str,
        amount: float,
        period: str,
        start_date: str,
        end_date: Optional[str] = None,
    ):
        self.budgets = [
            b for b in self.budgets if not (b.account == account and b.period == period)
        ]
        self.budgets.append(Budget(account, amount, period, start_date, end_date))
        self._save()

    def get_spending(self, account: str, from_date: str, to_date: str) -> float:
        """Sum of debit amounts to this account in date range (inclusive)."""
        total = 0.0
        from_dt = datetime.fromisoformat(from_date.replace(" ", "T"))
        to_dt = datetime.fromisoformat(to_date.replace(" ", "T"))
        for tx in self.ledger.get_transactions():
            if tx.dr == account:
                tx_dt = datetime.fromisoformat(tx.date.replace(" ", "T"))
                if from_dt <= tx_dt <= to_dt:
                    total += tx.amount
        return total

    def report(self) -> List[dict]:
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        end_of_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(
            seconds=1
        )
        end_of_month = end_of_month.strftime("%Y-%m-%d %H:%M:%S")

        report = []
        for b in self.budgets:
            actual = self.get_spending(b.account, start_of_month, end_of_month)
            remaining = b.amount - actual
            status = "✅ On track" if remaining >= 0 else "⚠️ Over budget"
            report.append(
                {
                    "account": b.account,
                    "budget": b.amount,
                    "actual": actual,
                    "remaining": remaining,
                    "status": status,
                }
            )
        return report


# ----------------------------------------------------------------------
# CLI with argparse and interactive loop
# ----------------------------------------------------------------------
def setup_parser():
    parser = argparse.ArgumentParser(description="Ledgerlogic 2.0", prog="ledger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add transaction")
    add_parser.add_argument("--desc", required=True)
    add_parser.add_argument("--amount", type=float, required=True)
    add_parser.add_argument("--dr", required=True)
    add_parser.add_argument("--cr", required=True)
    add_parser.add_argument("--comment", default="")

    del_parser = subparsers.add_parser("delete", help="Delete transaction by ID")
    del_parser.add_argument("id", type=int)

    edit_parser = subparsers.add_parser("edit", help="Edit transaction field")
    edit_parser.add_argument("id", type=int)
    edit_parser.add_argument("field", choices=["desc", "amount", "dr", "cr", "date", "comment"])
    edit_parser.add_argument("value")

    list_parser = subparsers.add_parser("list", help="List transactions")
    list_parser.add_argument("--sort", choices=["date", "amount"], default="date")

    balance_parser = subparsers.add_parser("balance", help="Show account balances")
    balance_parser.add_argument("--date", help="As of date (YYYY-MM-DD HH:MM:SS)")

    search_parser = subparsers.add_parser("search", help="Search transactions")
    search_parser.add_argument("--keyword")
    search_parser.add_argument("--min-amount", type=float)
    search_parser.add_argument("--max-amount", type=float)
    search_parser.add_argument("--account")
    search_parser.add_argument("--from-date")
    search_parser.add_argument("--to-date")

    subparsers.add_parser("undo", help="Undo last change")
    subparsers.add_parser("redo", help="Redo last undone change")

    macro_parser = subparsers.add_parser("macro", help="Manage macros")
    macro_sub = macro_parser.add_subparsers(dest="macro_cmd", required=True)
    macro_sub.add_parser("list")
    macro_add = macro_sub.add_parser("add")
    macro_add.add_argument("name")
    macro_add.add_argument("--dr", required=True)
    macro_add.add_argument("--cr", required=True)
    macro_remove = macro_sub.add_parser("remove")
    macro_remove.add_argument("name")
    macro_run = macro_sub.add_parser("run")
    macro_run.add_argument("name")
    macro_run.add_argument("amount", type=float)

    budget_parser = subparsers.add_parser("budget", help="Budget management")
    budget_sub = budget_parser.add_subparsers(dest="budget_cmd", required=True)
    budget_set = budget_sub.add_parser("set")
    budget_set.add_argument("account")
    budget_set.add_argument("amount", type=float)
    budget_set.add_argument("--period", choices=["weekly", "monthly", "yearly"], default="monthly")
    budget_set.add_argument("--start", default=datetime.now().strftime("%Y-%m-%d"))
    budget_set.add_argument("--end")
    budget_sub.add_parser("show")

    export_parser = subparsers.add_parser("export", help="Export transactions")
    export_parser.add_argument("filename")

    import_parser = subparsers.add_parser("import", help="Import transactions")
    import_parser.add_argument("filename")
    import_parser.add_argument("--replace", action="store_true")

    subparsers.add_parser("rebuild-ids", help="Renumber all transactions sequentially")

    return parser


def _dispatch_command(args, ledger, macros, budgets):
    """Execute a parsed command."""
    if args.command == "add":
        tx = ledger.add_transaction(args.desc, args.amount, args.dr, args.cr, args.comment)
        console.print(f"[green]Added ID {tx.id}: {tx.desc} (${tx.amount})[/green]")

    elif args.command == "delete":
        if ledger.delete_transaction(args.id):
            console.print(f"[green]Deleted transaction {args.id}[/green]")
        else:
            console.print(f"[red]ID {args.id} not found[/red]")

    elif args.command == "edit":
        val = args.value
        if args.field == "amount":
            try:
                val = float(val)
            except ValueError:
                console.print("[red]Amount must be a number[/red]")
                return
        if ledger.edit_transaction(args.id, args.field, val):
            console.print(f"[green]Edited {args.id} {args.field} -> {val}[/green]")
        else:
            console.print(f"[red]Transaction {args.id} not found[/red]")

    elif args.command == "list":
        txs = ledger.get_transactions(sort_by=args.sort)
        if not txs:
            console.print("[yellow]No transactions[/yellow]")
            return
        table = Table(title=f"Transactions (sorted by {args.sort})")
        table.add_column("ID", style="dim")
        table.add_column("Date")
        table.add_column("Description")
        table.add_column("Dr")
        table.add_column("Cr")
        table.add_column("Amount", justify="right")
        table.add_column("Comment", style="italic")
        for tx in txs:
            table.add_row(
                str(tx.id),
                tx.date,
                tx.desc,
                tx.dr,
                tx.cr,
                f"{tx.amount:.2f}",
                tx.comment[:30],
            )
        console.print(table)

    elif args.command == "balance":
        balances = ledger.get_balance(as_of=args.date)
        if not balances:
            console.print("[yellow]No transactions[/yellow]")
            return
        table = Table(title="Account Balances")
        table.add_column("Account")
        table.add_column("Balance", justify="right")
        for acc, amt in balances.items():
            color = "green" if amt >= 0 else "red"
            table.add_row(acc, f"[{color}]{amt:.2f}[/{color}]")
        console.print(table)

    elif args.command == "search":
        filters = {
            k: v
            for k, v in vars(args).items()
            if v is not None
            and k in ["keyword", "min_amount", "max_amount", "account", "from_date", "to_date"]
        }
        results = ledger.search(**filters)
        if not results:
            console.print("[yellow]No matches[/yellow]")
            return
        table = Table(title="Search Results")
        table.add_column("ID")
        table.add_column("Date")
        table.add_column("Description")
        table.add_column("Dr")
        table.add_column("Cr")
        table.add_column("Amount")
        for tx in results:
            table.add_row(
                str(tx.id), tx.date, tx.desc, tx.dr, tx.cr, f"{tx.amount:.2f}"
            )
        console.print(table)

    elif args.command == "undo":
        if ledger.undo():
            console.print("[green]Undo successful[/green]")
        else:
            console.print("[yellow]Nothing to undo[/yellow]")

    elif args.command == "redo":
        if ledger.redo():
            console.print("[green]Redo successful[/green]")
        else:
            console.print("[yellow]Nothing to redo[/yellow]")

    elif args.command == "macro":
        if args.macro_cmd == "list":
            for m in macros.list_macros():
                console.print(f"{m.name}: dr={m.dr}, cr={m.cr}")
        elif args.macro_cmd == "add":
            macros.add_macro(args.name, args.dr, args.cr)
            console.print(f"[green]Macro '{args.name}' added[/green]")
        elif args.macro_cmd == "remove":
            if macros.remove_macro(args.name):
                console.print(f"[green]Macro '{args.name}' removed[/green]")
            else:
                console.print(f"[red]Macro '{args.name}' not found[/red]")
        elif args.macro_cmd == "run":
            m = macros.get(args.name)
            if not m:
                console.print(f"[red]Macro '{args.name}' not found[/red]")
            else:
                tx = ledger.add_transaction(f"Macro: {args.name}", args.amount, m.dr, m.cr)
                console.print(f"[green]Ran macro '{args.name}': added ID {tx.id}[/green]")

    elif args.command == "budget":
        if args.budget_cmd == "set":
            budgets.set_budget(args.account, args.amount, args.period, args.start, args.end)
            console.print(
                f"[green]Budget set for {args.account}: ${args.amount} ({args.period})[/green]"
            )
        elif args.budget_cmd == "show":
            report = budgets.report()
            if not report:
                console.print("[yellow]No budgets set[/yellow]")
                return
            table = Table(title="Budget vs Actual (This Month)")
            table.add_column("Account")
            table.add_column("Budget", justify="right")
            table.add_column("Actual", justify="right")
            table.add_column("Remaining", justify="right")
            table.add_column("Status")
            for row in report:
                remaining = row["remaining"]
                color = "green" if remaining >= 0 else "red"
                table.add_row(
                    row["account"],
                    f"${row['budget']:.2f}",
                    f"${row['actual']:.2f}",
                    f"[{color}]${remaining:.2f}[/{color}]",
                    row["status"],
                )
            console.print(table)

    elif args.command == "export":
        ledger.export(args.filename)
        console.print(f"[green]Exported to {args.filename}[/green]")

    elif args.command == "import":
        try:
            ledger.import_transactions(args.filename, args.replace)
            console.print(f"[green]Imported from {args.filename}[/green]")
        except Exception as e:
            console.print(f"[red]Import failed: {e}[/red]")

    elif args.command == "rebuild-ids":
        ledger.rebuild_ids()
        console.print("[green]Transaction IDs rebuilt[/green]")

    else:
        console.print("[red]Unknown command[/red]")


def interactive_loop(ledger, macros, budgets):
    """Run an interactive command loop."""
    console.print("[bold cyan]Ledgerlogic 2.0 Interactive Mode[/bold cyan]")
    console.print("Type [yellow]help[/yellow] for commands, [yellow]q[/yellow] to quit.\n")
    parser = setup_parser()

    while True:
        try:
            raw = input(">> ").strip()
            if not raw:
                continue
            if raw.lower() in ("q", "quit", "exit"):
                ledger._save_checkpoint()
                console.print("[bold]Goodbye![/bold]")
                break
            if raw.lower() == "help":
                parser.print_help()
                continue

            try:
                args_list = shlex.split(raw)
            except ValueError as e:
                console.print(f"[red]Invalid input: {e}[/red]")
                continue

            
            try:
                parsed = parser.parse_args(args_list)
            except SystemExit:
                continue

            _dispatch_command(parsed, ledger, macros, budgets)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'q' to exit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    parser = setup_parser()
    ledger = Ledger()
    macros = MacroManager()
    budgets = BudgetManager(ledger)

    if len(sys.argv) == 1:
        interactive_loop(ledger, macros, budgets)
        return

    args = parser.parse_args()
    _dispatch_command(args, ledger, macros, budgets)


if __name__ == "__main__":
    main()