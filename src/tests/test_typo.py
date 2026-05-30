import pytest
import subprocess
import sys
import os
import re

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def run_cli(args, env=None):
    script_path = os.path.join(os.path.dirname(__file__), "..", "ledger.py")
    env_copy = os.environ.copy()
    if env:
        env_copy.update(env)
    env_copy["PYTHONIOENCODING"] = "utf-8"
    env_copy["PYTHONUTF8"] = "1"
    env_copy["TERM"] = "dumb"
    env_copy["FORCE_COLOR"] = "0"
    env_copy["NO_COLOR"] = "1"
    result = subprocess.run(
        [sys.executable, script_path] + args,
        capture_output=True,
        text=True,
        env=env_copy,
        encoding="utf-8",
        errors="replace"
    )
    return strip_ansi(result.stdout + result.stderr)

def run_interactive_commands(commands, env=None):
    script_path = os.path.join(os.path.dirname(__file__), "..", "ledger.py")
    env_copy = os.environ.copy()
    if env:
        env_copy.update(env)
    env_copy["PYTHONIOENCODING"] = "utf-8"
    env_copy["PYTHONUTF8"] = "1"
    env_copy["TERM"] = "dumb"
    env_copy["FORCE_COLOR"] = "0"
    env_copy["NO_COLOR"] = "1"
    input_data = "\n".join(commands + ["q"]) + "\n"
    result = subprocess.run(
        [sys.executable, script_path],
        input=input_data,
        capture_output=True,
        text=True,
        env=env_copy,
        encoding="utf-8",
        errors="replace"
    )
    return strip_ansi(result.stdout + result.stderr)

def test_typo_one_shot_mode(temp_dir):
    output = run_cli(
        ["ad", "--desc", "Coffee", "--amount", "3.5", "--dr", "Food", "--cr", "Cash"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "Unknown command: 'ad'. Did you mean 'add'?" in output   # note the period

def test_unknown_command_no_suggestion(temp_dir):
    output = run_cli(
        ["xyzxyz", "--desc", "Test"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "Unknown command: 'xyzxyz'. Use --help for usage." in output

def test_typo_interactive_mode(temp_dir):
    """Test that typo in interactive mode suggests correction."""
    commands = [
        "ad --desc Coffee --amount 3.5 --dr Food --cr Cash",
        "q"
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "Unknown command: 'ad'" in output
    assert "Did you mean 'add'?" in output

def test_unknown_command_no_suggestion(temp_dir):
    """Test that completely unknown command shows generic message."""
    output = run_cli(
        ["xyzxyz", "--desc", "Test"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "Unknown command: 'xyzxyz'" in output
    assert "Did you mean" not in output

def test_empty_input_interactive(temp_dir):
    """Test that empty input in interactive mode is ignored."""
    commands = ["", "q"]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # No error message, just continues
    assert "Error" not in output

def test_negative_amount_allowed(temp_dir):
    """Test that negative amounts can be added (accounting adjustment)."""
    output = run_cli(
        ["add", "--desc", "Refund", "--amount", "-10", "--dr", "Cash", "--cr", "Expense"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "Added ID 1" in output

def test_very_long_description(temp_dir):
    """Test that very long descriptions are handled."""
    long_desc = "A" * 1000
    output = run_cli(
        ["add", "--desc", long_desc, "--amount", "1", "--dr", "A", "--cr", "B"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "Added ID 1" in output

def test_invalid_date_format(temp_dir):
    """Test that invalid date in edit is handled gracefully."""
    # First add a transaction
    run_cli(
        ["add", "--desc", "Test", "--amount", "10", "--dr", "A", "--cr", "B"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    # Try to edit with invalid date (should work, but date will be stored as string)
    output = run_cli(
        ["edit", "1", "date", "not-a-date"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    # No validation, so should succeed
    assert "Edited 1 date -> not-a-date" in output

def test_search_no_results(temp_dir):
    """Test search returns empty but friendly message."""
    output = run_cli(
        ["search", "--keyword", "NothingHere"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "No matches" in output