#!/usr/bin/env python3
"""U3 local autograder: trusted classroom submissions only, not a security sandbox."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAW_RECORDS = [
    {"record_id": "R01", "day": "周一", "minutes": "25"},
    {"record_id": "R02", "day": "周二", "minutes": " 35 "},
    {"record_id": "R03", "day": "周三", "minutes": ""},
    {"record_id": "R04", "day": "周四", "minutes": "30分钟"},
    {"record_id": "R05", "day": "周二", "minutes": "35"},
    {"record_id": "R06", "day": "周五", "minutes": "abc"},
    {"record_id": "R07", "day": "周六", "minutes": "0"},
]

BLOCKED_NAMES = {
    "__import__", "eval", "exec", "compile", "open", "input",
    "breakpoint", "help", "dir", "globals", "locals", "vars",
}
BLOCKED_ATTRS = {
    "system", "popen", "remove", "unlink", "rmdir", "chmod",
    "write_text", "write_bytes", "read_text", "read_bytes",
}

WORKER = r'''
import importlib.util
import json
import sys

candidate_path = sys.argv[1]
raw_records = [
    {"record_id": "R01", "day": "周一", "minutes": "25"},
    {"record_id": "R02", "day": "周二", "minutes": " 35 "},
    {"record_id": "R03", "day": "周三", "minutes": ""},
    {"record_id": "R04", "day": "周四", "minutes": "30分钟"},
    {"record_id": "R05", "day": "周二", "minutes": "35"},
    {"record_id": "R06", "day": "周五", "minutes": "abc"},
    {"record_id": "R07", "day": "周六", "minutes": "0"},
]

spec = importlib.util.spec_from_file_location("student_submission", candidate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

clean_cases = []
for raw in ["25", " 35 ", "30分钟", "", "abc", "-5", "0"]:
    value = module.clean_minutes(raw)
    clean_cases.append({"raw": raw, "value": value})

original_copy = [dict(row) for row in raw_records]
clean_records, issues = module.transform_records(raw_records)
summary = None
if hasattr(module, "summarize_records"):
    summary = module.summarize_records(clean_records, issues)

print(json.dumps({
    "clean_cases": clean_cases,
    "clean_records": clean_records,
    "issues": issues,
    "summary": summary,
    "raw_unchanged": raw_records == original_copy,
}, ensure_ascii=False, default=str))
'''


def static_check(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"语法错误：第 {exc.lineno} 行 {exc.msg}"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            issues.append("检测到 import：课堂版评分器不允许导入外部模块。")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
                issues.append(f"检测到受限调用：{node.func.id}。")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRS:
            issues.append(f"检测到受限属性调用：.{node.attr}。")
    return issues


def run_student(path: Path) -> tuple[dict | None, str | None]:
    with tempfile.TemporaryDirectory(prefix="u3_grade_") as tmp:
        worker_path = Path(tmp) / "worker.py"
        worker_path.write_text(WORKER, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(worker_path), str(path.resolve())],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return None, "运行超时：请检查循环是否能结束。"
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            return None, "运行错误：" + (detail[-1] if detail else "未知错误")
        try:
            return json.loads(proc.stdout), None
        except json.JSONDecodeError:
            return None, "输出无法解析为测试结果；请检查函数返回值是否可序列化。"


def is_issue_reason(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_clean_pair(value, expected_value=None, allow_issue=False) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return False
    clean_value, issue = value
    if allow_issue and clean_value is None:
        return is_issue_reason(issue)
    return clean_value == expected_value and (issue is None or issue == "")


def grade(result: dict) -> tuple[int, list[dict], list[str]]:
    checks: list[dict] = []
    feedback: list[str] = []

    clean_cases = result.get("clean_cases", [])
    expected = [
        ("25", 25, False),
        (" 35 ", 35, False),
        ("30分钟", 30, True),
        ("", None, True),
        ("abc", None, True),
        ("-5", None, True),
        ("0", 0, False),
    ]
    clean_pass = 0
    for actual, (raw, expected_value, flexible) in zip(clean_cases, expected):
        value = actual.get("value")
        ok = is_clean_pair(value, expected_value) if not flexible else (
            is_clean_pair(value, expected_value) or is_clean_pair(value, allow_issue=True)
        )
        clean_pass += int(ok)
        checks.append({"name": f"单值：{raw or '空值'}", "passed": ok})
    if clean_pass < len(expected):
        feedback.append("先检查 clean_minutes：空值、无效文本和负数应保留原因，不能默默变成 0。")

    clean_records = result.get("clean_records")
    issues = result.get("issues")
    batch_ok = isinstance(clean_records, list) and isinstance(issues, list)
    if batch_ok:
        total_count_ok = len(clean_records) + len(issues) == len(RAW_RECORDS)
        valid_shape_ok = all(
            isinstance(row, dict) and isinstance(row.get("minutes"), int)
            and row.get("minutes") >= 0 and "record_id" in row
            for row in clean_records
        )
        batch_ok = total_count_ok and valid_shape_ok and 4 <= len(clean_records) <= 5
    checks.append({"name": "批量分流：有效列表与问题列表", "passed": batch_ok})
    if not batch_ok:
        feedback.append("检查 transform_records：每条记录必须进入有效列表或问题日志，且有效记录需保留 record_id。")

    log_ok = isinstance(issues, list) and all(
        isinstance(row, dict) and row.get("record_id") and "raw_value" in row and is_issue_reason(row.get("reason"))
        for row in issues
    )
    checks.append({"name": "质量日志：编号、原始值、原因", "passed": log_ok})
    if not log_ok:
        feedback.append("问题日志至少保留 record_id、raw_value 和非空 reason。")

    raw_ok = result.get("raw_unchanged") is True
    checks.append({"name": "原始记录保持不变", "passed": raw_ok})
    if not raw_ok:
        feedback.append("不要覆盖 raw_records；请将清洗结果保存到新列表。")

    summary = result.get("summary")
    summary_ok = True
    if summary is not None:
        summary_ok = isinstance(summary, dict) and all(
            key in summary for key in ("valid_count", "issue_count", "total_minutes", "average_minutes")
        )
    checks.append({"name": "汇总字段口径", "passed": summary_ok})
    if not summary_ok:
        feedback.append("如果提供 summarize_records，应返回 valid_count、issue_count、total_minutes、average_minutes。")

    score = round(
        30 * clean_pass / len(expected)
        + 25 * int(batch_ok)
        + 20 * int(log_ok)
        + 15 * int(raw_ok)
        + 10 * int(summary_ok)
    )
    return score, checks, feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="U3 本地自动评分器（仅限可信课堂代码）")
    parser.add_argument("submission", type=Path)
    parser.add_argument("--json-result", type=Path)
    args = parser.parse_args()

    static_issues = static_check(args.submission)
    if static_issues:
        payload = {"score": 0, "static_issues": static_issues, "checks": [], "feedback": ["请先移除受限语法，再重新提交。"]}
    else:
        result, error = run_student(args.submission)
        if error:
            payload = {"score": 0, "static_issues": [], "checks": [], "feedback": [error]}
        else:
            score, checks, feedback = grade(result or {})
            payload = {"score": score, "static_issues": [], "checks": checks, "feedback": feedback}

    print(f"U3 自动评分结果：{payload['score']}/100")
    for check in payload.get("checks", []):
        print(("通过" if check["passed"] else "未通过") + "｜" + check["name"])
    for item in payload.get("static_issues", []) + payload.get("feedback", []):
        print("建议｜" + item)
    if args.json_result:
        args.json_result.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
