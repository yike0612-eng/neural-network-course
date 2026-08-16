#!/usr/bin/env python3
"""U4 local autograder for trusted classroom submissions; not a security sandbox."""
from __future__ import annotations

import argparse
import ast
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_CSV = """date,space,visits,minutes
2026-04-01,东区,42,35
2026-04-02,东区,,40
2026-04-03,西区,38,abc
2026-04-03,西区,38,45
2026-04-04,东区,51,50
2026-04-05,西区,44, 30 
"""

BLOCKED_NAMES = {"__import__", "eval", "exec", "compile", "input", "breakpoint"}
BLOCKED_ATTRS = {"system", "popen", "remove", "unlink", "rmdir", "chmod", "write_text", "write_bytes"}

WORKER = r'''
import importlib.util
import json
import sys

path, csv_path = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("student_submission", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = module.read_rows(csv_path)
original = [dict(row) for row in rows]
valid, issues, stats = module.clean_rows(rows)
groups = module.group_summary(valid)
print(json.dumps({
    "rows": rows,
    "original": original,
    "valid": valid,
    "issues": issues,
    "stats": stats,
    "groups": groups,
}, ensure_ascii=False, default=str))
'''


def static_check(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"语法错误：第 {exc.lineno} 行 {exc.msg}"]
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name != "csv":
                    issues.append(f"只允许课堂基础导入 csv，发现 {alias.name}。")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
            issues.append(f"检测到受限调用：{node.func.id}。")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRS:
            issues.append(f"检测到受限属性调用：.{node.attr}。")
    return issues


def write_csv(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def run_submission(submission: Path, csv_text: str) -> tuple[dict | None, str | None]:
    with tempfile.TemporaryDirectory(prefix="u4_grade_") as tmp:
        root = Path(tmp)
        worker_path = root / "worker.py"
        csv_path = root / "reading_space_raw.csv"
        worker_path.write_text(WORKER, encoding="utf-8")
        write_csv(csv_path, csv_text)
        try:
            proc = subprocess.run(
                [sys.executable, str(worker_path), str(submission.resolve()), str(csv_path)],
                capture_output=True, text=True, timeout=5, cwd=root,
            )
        except subprocess.TimeoutExpired:
            return None, "运行超时：请检查文件读取或循环是否能结束。"
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            return None, "运行错误：" + (detail[-1] if detail else "未知错误")
        try:
            return json.loads(proc.stdout), None
        except json.JSONDecodeError:
            return None, "测试输出无法解析；请检查函数返回值是否可序列化。"


def has_reason(item: dict) -> bool:
    return isinstance(item, dict) and bool(str(item.get("reason", "")).strip())


def grade(result: dict) -> tuple[int, list[dict], list[str]]:
    checks = []
    feedback = []
    rows = result.get("rows", [])
    valid = result.get("valid", [])
    issues = result.get("issues", [])
    stats = result.get("stats", {})
    groups = result.get("groups", {})

    read_ok = len(rows) == 6 and all(isinstance(row, dict) for row in rows) and {"date", "space", "visits", "minutes"}.issubset(rows[0])
    checks.append({"name": "CSV读取：6条字段记录", "passed": read_ok})
    if not read_ok:
        feedback.append("先检查文件路径、CSV首行字段和 DictReader 读取结果。")

    valid_shapes = all(
        isinstance(row, dict) and isinstance(row.get("visits"), int) and row["visits"] >= 0
        and isinstance(row.get("minutes"), int) and row["minutes"] >= 0
        and "space" in row for row in valid
    )
    clean_ok = valid_shapes and 2 <= len(valid) <= 5
    checks.append({"name": "字段清洗：非负整数与有效记录", "passed": clean_ok})
    if not clean_ok:
        feedback.append("对 visits 和 minutes 做显式类型转换；空值、无效文本、非法数值应进入问题日志。")

    issue_ok = isinstance(issues, list) and len(issues) >= 1 and all(has_reason(item) for item in issues)
    log_fields_ok = issue_ok and all(
        any(key in item for key in ("record_index", "row", "record_id"))
        and any(key in item for key in ("field", "column"))
        and any(key in item for key in ("raw_value", "raw"))
        for item in issues
    )
    checks.append({"name": "质量日志：字段、原始值、原因", "passed": log_fields_ok})
    if not log_fields_ok:
        feedback.append("问题日志需保留记录位置或编号、字段、原始值和原因。")

    stats_ok = isinstance(stats, dict) and all(key in stats for key in ("raw_count", "valid_count", "issue_count"))
    count_ok = stats_ok and stats.get("raw_count") == len(rows) and stats.get("valid_count") == len(valid)
    checks.append({"name": "清洗统计：记录去向可解释", "passed": count_ok})
    if not count_ok:
        feedback.append("输出原始行数、有效行数和问题行数，并说明一行包含多个问题时的计数口径。")

    raw_ok = result.get("original") == rows
    checks.append({"name": "原始记录未被覆盖", "passed": raw_ok})
    if not raw_ok:
        feedback.append("请复制记录或建立新结果结构，不要修改原始 CSV 读取结果。")

    group_ok = isinstance(groups, dict) and len(groups) >= 1 and all(
        isinstance(item, dict) and all(key in item for key in ("valid_count", "total_visits", "total_minutes", "average_minutes"))
        for item in groups.values()
    )
    checks.append({"name": "分组汇总：有效数、总量、平均值", "passed": group_ok})
    if not group_ok:
        feedback.append("只对有效记录按 space 分组，并为每组报告有效记录数、总访问次数、总分钟数和平均值。")

    score = round(
        20 * int(read_ok)
        + 25 * int(clean_ok)
        + 20 * int(log_fields_ok)
        + 20 * int(count_ok)
        + 5 * int(raw_ok)
        + 10 * int(group_ok)
    )
    return score, checks, feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="U4 CSV项目本地自动评分器")
    parser.add_argument("submission", type=Path)
    parser.add_argument("--csv-path", type=Path)
    parser.add_argument("--json-result", type=Path)
    args = parser.parse_args()

    csv_text = args.csv_path.read_text(encoding="utf-8-sig") if args.csv_path else BASE_CSV
    static_issues = static_check(args.submission)
    if static_issues:
        payload = {"score": 0, "static_issues": static_issues, "checks": [], "feedback": ["请移除受限语法后再提交。"]}
    else:
        result, error = run_submission(args.submission, csv_text)
        if error:
            payload = {"score": 0, "static_issues": [], "checks": [], "feedback": [error]}
        else:
            score, checks, feedback = grade(result or {})
            payload = {"score": score, "static_issues": [], "checks": checks, "feedback": feedback}

    print(f"U4 自动评分结果：{payload['score']}/100")
    for item in payload.get("checks", []):
        print(("通过" if item["passed"] else "未通过") + "｜" + item["name"])
    for item in payload.get("static_issues", []) + payload.get("feedback", []):
        print("建议｜" + item)
    if args.json_result:
        args.json_result.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
