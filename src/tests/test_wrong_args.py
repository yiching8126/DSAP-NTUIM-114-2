import pytest
import re
from tests.test_cli import run_interactive_commands, strip_ansi

def test_wrong_arg_add_desk(temp_dir):
    """Typo '--desk' instead of '--desc' should not exit interactive mode."""
    commands = [
        'add --desk Coffee --amount 3.5 --dr Food --cr Cash',
        'add --desc Valid --amount 1 --dr A --cr B',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # Should show error message for --desk
    assert "error:" in output or "argument" in output
    # Should still execute the valid add command
    assert "Added ID" in output
    # Should list at least one transaction
    assert "Valid" in output

def test_wrong_arg_add_dr_missing(temp_dir):
    """Missing --dr flag (not a typo, but missing required)."""
    commands = [
        'add --desc Test --amount 10 --cr Cash',
        'add --desc Valid3 --amount 1 --dr X --cr Y',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "error:" in output
    assert "Valid3" in output

def test_wrong_arg_add_invalid_flag(temp_dir):
    """Completely invalid flag like --xyz."""
    commands = [
        'add --desc Test --amount 10 --dr A --cr B --xyz 123',
        'add --desc AfterError --amount 2 --dr C --cr D',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "unrecognized arguments" in output or "error" in output
    assert "AfterError" in output

def test_wrong_arg_list_sort_typo(temp_dir):
    """Typo: list --srt instead of --sort."""
    commands = [
        'add --desc Base --amount 1 --dr A --cr B',
        'list --srt amount',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "error" in output or "unrecognized" in output
    # The second list (without typo) should work
    assert "Base" in output

def test_wrong_arg_add_amoun(temp_dir):
    """Use a completely invalid flag '--xyz' to force an error."""
    commands = [
        'add --desc Test --xyz 10 --dr A --cr B',
        'add --desc Valid2 --amount 5 --dr C --cr D',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # First command should produce an error
    assert "error" in output.lower() or "unrecognized" in output.lower()
    # Second command should succeed
    assert "Valid2" in output
    assert "Added ID" in output

def test_wrong_arg_edit_field_typo(temp_dir):
    """Edit command with typo in field name (invalid choice)."""
    commands = [
        'add --desc Original --amount 10 --dr A --cr B',
        'edit 1 descrption NewDesc',   # invalid field
        'edit 1 desc NewDesc2',        # correct field
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # First edit should produce an invalid choice error
    assert "invalid choice" in output.lower()
    # Second edit should succeed and the list should show NewDesc2
    assert "NewDesc2" in output
    # Note: 'Original' still appears in the initial add message, so we cannot assert it is absent.
    # The test only verifies that the error is caught and the second edit works.

def test_wrong_arg_budget_period_typo(temp_dir):
    """Budget set with typo in --period."""
    commands = [
        'budget set Food 100 --period monthy',  # 'monthy' instead of 'monthly'
        'budget set Food 200 --period monthly',
        'budget show',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # Should error on first, then second works
    assert "error" in output or "invalid choice" in output
    assert "200.00" in output

def test_wrong_arg_macro_run_typo(temp_dir):
    """Macro run with typo in macro name (should suggest or error but not exit)."""
    commands = [
        'macro add test --dr Food --cr Cash',
        'macro run tes 10',   # 'tes' instead of 'test'
        'macro run test 20',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "not found" in output or "Unknown" in output
    assert "20.00" in output

def test_wrong_arg_search_typo(temp_dir):
    """Search with typo in flag."""
    commands = [
        'add --desc Target --amount 5 --dr A --cr B',
        'search --keywrd Target',  # typo: --keywrd
        'search --keyword Target',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "error" in output
    assert "Target" in output

def test_interactive_continues_after_multiple_errors(temp_dir):
    """Multiple wrong commands in a row should still keep REPL alive."""
    commands = [
        'add --desk Bad1',
        'add --amoun 10',
        'list',
        'add --desc Good --amount 1 --dr A --cr B',
        'list',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    # After all errors, the final add and list should work
    assert "Good" in output
    assert "Added ID" in output

def test_q_still_exits_after_errors(temp_dir):
    """After errors, typing 'q' should exit gracefully."""
    commands = [
        'add --desk Bad',
        'q'
    ]
    output = run_interactive_commands(commands, env={"LEDGER_DATA_DIR": temp_dir})
    assert "Goodbye" in output or "exit" in output.lower()