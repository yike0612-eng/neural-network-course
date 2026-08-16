#!/usr/bin/env python3
"""U6 local project validator for trusted classroom submissions; not a security sandbox."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_RECORDS = [
    {"category": " 东区 ", "value": "45分钟", "period": "周一"},
    {"category": "西区", "value": " 30 ", "period": "周二"},
    {"category": "东区", "value": "", "period": "周三"},
    {"category": "西区", "value": "abc", "period": "周四"},
    {"category": "东区", "value": "-5", "period": "周五"},
    {"category": "", "value": "20", "period": "周六"},
]

SENSITIVITY_RECORDS = [
    {"category": "东区", "value": "60", "period": "周一"},
    {"category": "西区", "value": "30", "period": "周二"},
]

BLOCKED_NAMES = {"__import__", "eval", "exec", "compile", "input", "breakpoint"}
BLOCKED_ATTRS = {"system", "popen", "remove", "unlink", "rmdir", "chmod", "write_text", "write_bytes"}

WORKER = r'''
import importlib.util
import json
import sys

submission, records_text, sensitivity_text = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("student_submission", submission)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def run(records):
    original = [dict(item) for item in records]
    valid, issues, stats = module.process_records(records)
    groups = module.group_summary(valid)
    chart = module.build_chart_spec(groups)
    return {
        "original_after": records,
        "original_copy": original,
        "valid": valid,
        "issues": issues,
        "stats": stats,
        "groups": groups,
        "chart": chart,
    }

base = json.loads(records_text)
sensitivity = json.loads(sensitivity_text)
payload = {
    "metadata": module.project_metadata(),
    "base": run(base),
    "sensitivity": run(sensitivity),
}
print(json.dumps(payload, ensure_ascii=False, default=str))
'''


def static_check(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"语法错误：第 {exc.lineno} 行 {exc.msg}"]
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            issues.append("自动验收提交文件不允许导入模块；请只保留课堂函数接口。")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
            issues.append(f"检测到受限调用：{node.func.id}。")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRS:
            issues.append(f"检测到受限属性调用：.{node.attr}。")
    return issues


def run_submission(submission: Path) -> tuple[dict | None, str | None]:
    with tempfile.TemporaryDirectory(prefix="u6_grade_") as tmp:
        root = Path(tmp)
        worker = root / "worker.py"
        worker.write_text(WORKER, encoding="utf-8")
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(worker),
                    str(submission.resolve()),
                    json.dumps(BASE_RECORDS, ensure_ascii=False),
                    json.dumps(SENSITIVITY_RECORDS, ensure_ascii=False),
                ],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=root,
            )
        except subprocess.TimeoutExpired:
            return None, "运行超时：请检查循环、文件等待或函数调用是否能结束。"
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            return None, "运行错误：" + (detail[-1] if detail else "未知错误")
        try:
            return json.loads(proc.stdout), None
        except json.JSONDecodeError:
            return None, "测试输出无法解析；请检查函数返回值是否可序列化。"


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "请填写" not in value


def issue_complete(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    return all(key in item for key in ("record_index", "field", "raw_value", "reason")) and nonempty_string(str(item.get("reason", "")))


def grade(payload: dict) -> tuple[int, list[dict], list[str]]:
    checks: list[dict] = []
    feedback: list[str] = []
    metadata = payload.get("metadata", {})
    base = payload.get("base", {})
    sensitivity = payload.get("sensitivity", {})

    meta_keys = ("question", "data_scope", "core_metric", "chart_type", "unit", "recommendation", "boundary")
    metadata_ok = (
        isinstance(metadata, dict)
        and all(nonempty_string(metadata.get(key)) for key in meta_keys)
        and metadata.get("approved_data") is True
        and metadata.get("personal_data_collected") is False
        and str(metadata.get("chart_type")) in {"bar", "line"}
    )
    checks.append({"name": "项目声明：批准数据、问题、指标、建议和边界", "passed": metadata_ok})
    if not metadata_ok:
        feedback.append("完善 project_metadata：明确问题、数据范围、指标、图表、单位、谨慎建议和边界，并确认只用批准数据。")

    valid = base.get("valid", [])
    issues = base.get("issues", [])
    stats = base.get("stats", {})
    groups = base.get("groups", {})
    chart = base.get("chart", {})

    clean_ok = (
        isinstance(valid, list)
        and len(valid) == 2
        and all(isinstance(item, dict) and isinstance(item.get("category"), str) and item["category"].strip()
                and isinstance(item.get("value"), (int, float)) and item["value"] >= 0
                and "period" in item for item in valid)
        and {item["category"] for item in valid} == {"东区", "西区"}
        and {item["value"] for item in valid} == {45, 30}
    )
    checks.append({"name": "单条与批量清洗：规范类别、非负数值、有效分流", "passed": clean_ok})
    if not clean_ok:
        feedback.append("检查 clean_record：清除类别和数值两端空格，处理‘分钟’，并让空值、文本、负值进入问题日志。")

    issue_ok = isinstance(issues, list) and len(issues) >= 3 and all(issue_complete(item) for item in issues)
    checks.append({"name": "质量日志：记录位置、字段、原始值、原因", "passed": issue_ok})
    if not issue_ok:
        feedback.append("问题日志至少保留 record_index、field、raw_value 和 reason；不要静默删除无效记录。")

    stats_ok = (
        isinstance(stats, dict)
        and stats.get("raw_count") == len(BASE_RECORDS)
        and stats.get("valid_count") == len(valid)
        and stats.get("issue_count") == len(issues)
        and base.get("original_after") == base.get("original_copy")
    )
    checks.append({"name": "记录去向与原始保护：原始、有效、问题可解释", "passed": stats_ok})
    if not stats_ok:
        feedback.append("统计原始、有效和问题记录数；不要修改 process_records 接收到的原始列表或原始字典。")

    group_ok = (
        isinstance(groups, dict)
        and set(groups) == {"东区", "西区"}
        and all(isinstance(item, dict) and all(key in item for key in ("valid_count", "total_value", "average_value")) for item in groups.values())
        and groups["东区"].get("valid_count") == 1
        and groups["东区"].get("total_value") == 45
        and groups["西区"].get("average_value") == 30
    )
    checks.append({"name": "分组汇总：有效数、总量、平均值仅来自有效记录", "passed": group_ok})
    if not group_ok:
        feedback.append("group_summary 只汇总有效记录，并为每类输出 valid_count、total_value 和 average_value。")

    chart_ok = (
        isinstance(chart, dict)
        and str(chart.get("chart_type")) in {"bar", "line"}
        and all(nonempty_string(chart.get(key)) for key in ("title", "x_label", "y_label", "unit", "scope_note"))
        and isinstance(chart.get("labels"), list)
        and isinstance(chart.get("values"), list)
        and len(chart["labels"]) == len(chart["values"]) >= 1
        and set(chart["labels"]) == set(groups)
    )
    checks.append({"name": "主图规格：类型、标题、标签、单位、范围与真实汇总", "passed": chart_ok})
    if not chart_ok:
        feedback.append("build_chart_spec 必须从 summary 生成 labels 和 values，并注明标题、轴/标签、单位与范围边界。")

    sensitivity_stats = sensitivity.get("stats", {})
    sensitivity_groups = sensitivity.get("groups", {})
    sensitivity_ok = (
        sensitivity_stats.get("valid_count") == 2
        and sensitivity_groups.get("东区", {}).get("total_value") == 60
        and sensitivity_groups.get("东区", {}).get("total_value") != groups.get("东区", {}).get("total_value")
    )
    checks.append({"name": "输入变化测试：修改模拟输入后汇总发生可解释变化", "passed": sensitivity_ok})
    if not sensitivity_ok:
        feedback.append("不要在代码中写死结果；改变一条批准的模拟输入后，汇总和图表规格应基于新记录计算。")

    score = (
        15 * int(metadata_ok)
        + 25 * int(clean_ok)
        + 15 * int(issue_ok)
        + 15 * int(stats_ok)
        + 15 * int(group_ok)
        + 10 * int(chart_ok)
        + 5 * int(sensitivity_ok)
    )
    return score, checks, feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="U6 校园数据微项目本地自动验收器")
    parser.add_argument("submission", type=Path, help="学生 u6_submission.py 文件")
    parser.add_argument("--json-result", type=Path, help="可选：写入 JSON 结果")
    args = parser.parse_args()

    static_issues = static_check(args.submission)
    if static_issues:
        payload = {"score": 0, "static_issues": static_issues, "checks": [], "feedback": ["请移除受限语法后再提交。"]}
    else:
        result, error = run_submission(args.submission)
        if error:
            payload = {"score": 0, "static_issues": [], "checks": [], "feedback": [error]}
        else:
            score, checks, feedback = grade(result or {})
            payload = {"score": score, "static_issues": [], "checks": checks, "feedback": feedback}

    print(f"U6 自动验收结果：{payload['score']}/100")
    for item in payload.get("checks", []):
        print(("通过" if item["passed"] else "未通过") + "｜" + item["name"])
    for item in payload.get("static_issues", []) + payload.get("feedback", []):
        print("建议｜" + item)
    if args.json_result:
        args.json_result.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
