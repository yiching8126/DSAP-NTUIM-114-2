# you asked

message time: 2026-05-06 12:38:58

make a user oriented feature breakdown

---

# deepseek response

Below is a **user‑oriented feature breakdown** of your accounting CLI. It explains what the program does from an end‑user perspective, grouped by real‑world tasks. You can paste this directly into your **Final Report** or **User Manual** section.

---

# User‑Oriented Feature Breakdown

## 1. Recording Transactions (Daily Bookkeeping)

| You want to... | Command | Example |
|----------------|---------|---------|
| Record a full double‑entry transaction | `add` (interactive) | `add` → then enter description, amount, debit account, credit account, optional comment |
| Quickly enter a recurring‑type expense without typing accounts | `misc <amount>` | `misc 12.50` (debits `Miscellaneous`, credits `Cash`) |
| Use a saved macro (predefined account pairs) | `macro <name> <amount>` | `macro lunch 8.50` (debits `Food`, credits `Cash`) |
| Add or edit a comment on an existing transaction | `comment <id> <text>` | `comment 3 Paid with credit card, receipt lost` |
| Modify any field of a past transaction | `edit <id> <field> <new_value>` | `edit 3 amount 49.99` or `edit 3 description "New keyboard"` |

**Fields you can edit**: `description`, `amount`, `dr` (debit account), `cr` (credit account), `date`, `comment`

---

## 2. Viewing & Reporting

| You want to... | Command | Example |
|----------------|---------|---------|
| See all transactions in a table | `list` | `list` (sorts by date) |
| Sort transactions by amount | `list amount` | `list amount` |
| See current balance of each account | `balance` | `balance` |
| Search transactions by keyword | `search <keyword>` | `search coffee` |
| Search with multiple filters (interactive) | `search` (then answer prompts) | `search` → enter min amount, max amount, account, keyword |

---

## 3. Correcting Mistakes (Undo/Redo)

| You want to... | Command |
|----------------|---------|
| Revert the last change (add, delete, edit, import) | `undo` |
| Put back a change you just undid | `redo` |

> **Note**: The program keeps a history of the last 20 actions.

---

## 4. Automating Recurring Transactions

| You want to... | Command | Example |
|----------------|---------|---------|
| Create a recurring rule | `recur add <desc> <amt> <dr> <cr> <interval_days>` | `recur add "Monthly Rent" 1500 Rent Cash 30` |
| List all recurring rules | `recur list` | `recur list` |
| Delete a recurring rule | `recur delete <id>` | `recur delete 2` |
| Manually trigger due recurring transactions | `recur run` | `recur run` (adds all transactions whose next due date ≤ today) |

> **How it works**: Each rule has a `next_due` date. When you run `recur run`, the program adds the transaction and automatically updates the due date (+ interval days). Recurring transactions appear in the main ledger with a `Recurring:` prefix in the description.

---

## 5. Budget Tracking

| You want to... | Command | Example |
|----------------|---------|---------|
| Set a monthly budget for an expense account | `budget set <account> <amount>` | `budget set Food 500` |
| View budget vs actual spending (current month) | `budget show` | `budget show` |

> **What you see**: A table with budget, actual spending, remaining amount, and a status (✅ On track / ⚠️ Over budget). A summary panel shows total budget vs total actual.

---

## 6. Data Backup & Portability

| You want to... | Command | Example |
|----------------|---------|---------|
| Save all transactions to a JSON or CSV file | `export <filename>` | `export backup.json` or `export report.csv` |
| Load transactions from a file (merge) | `import <filename>` | `import old_ledger.json` |
| Replace current data with a file (no merge) | `import --replace <filename>` | `import --replace backup.json` |

> All import/export operations preserve comments and all fields. CSV includes a `comment` column.

---

## 7. Performance & Testing (Power User)

| You want to... | Command |
|----------------|---------|
| Compare speed of list vs dict storage | `perftest` (requires pre‑generated `test_data.json`) |
| Run built‑in unit tests (if you added the test suite) | `test` |

---

## 8. Getting Help & Exiting

| You want to... | Command |
|----------------|---------|
| Show the full command reference | `help` |
| Quit the program (auto‑saves) | `exit` |

---

## Summary of All Commands

```
add           misc          macro         list          balance
delete        edit          comment       undo          redo
recur add     recur list    recur delete  recur run
budget set    budget show
search        export        import        perftest      help
exit
```

---

This breakdown makes your CLI look like a thoroughly planned, user‑tested application – exactly what a month‑long project should deliver.