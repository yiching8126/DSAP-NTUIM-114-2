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

def test_benchmark_runs(temp_dir):
    """测试 benchmark 命令能够正常运行并输出结果表格"""
    output = run_cli(
        ["benchmark", "--num", "10"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    # 验证输出包含关键表头和结论
    assert "List vs Dict Performance" in output
    assert "Speedup" in output
    assert "Conclusion" in output
    # 验证两个操作都被执行（查找和删除）
    # The Rich table may wrap "1000 random lookups" across lines
    assert "random" in output and "lookups" in output
    assert "Delete" in output

def test_benchmark_default_num(temp_dir):
    """测试不带 --num 参数时使用默认值 10000"""
    output = run_cli(
        ["benchmark"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    assert "List vs Dict Performance (num_transactions=10000)" in output

def test_benchmark_small_num(temp_dir):
    """测试非常小的交易数量（例如 5）"""
    output = run_cli(
        ["benchmark", "--num", "5"],
        env={"LEDGER_DATA_DIR": temp_dir}
    )
    # 即使交易数量很少，删除操作需要删除500个，但只有5个，所以会删除全部
    # 程序不应崩溃，仍然输出表格
    assert "List vs Dict Performance" in output