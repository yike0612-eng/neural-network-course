#!/usr/bin/env python3
"""U5 local autograder for trusted classroom submissions; not a security sandbox."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BLOCKED_NAMES = {"__import__", "eval", "exec", "compile", "input", "breakpoint", "open"}
BLOCKED_ATTRS = {"system", "popen", "remove", "unlink", "rmdir", "chmod", "write_text", "write_bytes"}


def static_check(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"语法错误：第 {exc.lineno} 行 {exc.msg}"]
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name not in {"statistics", "math"}:
                    issues.append(f"课堂自动评分只允许 statistics 或 math，发现 {alias.name}。")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_NAMES:
            issues.append(f"检测到受限调用：{node.func.id}。")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTRS:
            issues.append(f"检测到受限属性调用：.{node.attr}。")
    return issues


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("student_submission", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_checks(path: Path) -> tuple[dict | None, str | None]:
    try:
        module = load_module(path)
        values = [25, 35, 40, 30, 50, 45, 35]
        base = module.summarize(values)
        outlier = module.summarize(values + [500])
        empty = module.summarize([])
        choices = {
            "time_series": module.choose_chart("change", "time_series"),
            "category": module.choose_chart("compare", "categories"),
            "composition": module.choose_chart("composition", "categories"),
        }
        story = module.build_story("一周模拟阅读分钟如何变化？", values, "change", "time_series")
        changed = module.build_story("一周模拟阅读分钟如何变化？", values + [60], "change", "time_series")
        return {
            "base": base,
            "outlier": outlier,
            "empty": empty,
            "choices": choices,
            "story": story,
            "changed": changed,
        }, None
    except Exception as exc:  # classroom diagnostic boundary
        return None, f"运行错误：{type(exc).__name__}: {exc}"


def check_number(value, expected, tolerance=1e-6):
    return isinstance(value, (int, float)) and abs(float(value) - expected) <= tolerance


def grade(payload: dict) -> tuple[int, list[dict], list[str]]:
    checks = []
    feedback = []
    base = payload.get("base", {})
    outlier = payload.get("outlier", {})
    empty = payload.get("empty", {})
    choices = payload.get("choices", {})
    story = payload.get("story", {})
    changed = payload.get("changed", {})

    stats_ok = (
        base.get("count") == 7 and base.get("total") == 260
        and check_number(base.get("mean"), 260 / 7)
        and check_number(base.get("median"), 35)
        and outlier.get("count") == 8
        and empty.get("count") == 0
        and empty.get("mean") is None
    )
    checks.append({"name": "统计量：均值、中位数、总量、数量和空列表", "passed": stats_ok})
    if not stats_ok:
        feedback.append("检查 count、total、mean、median；空列表应有明确且可解释的处理。")

    choices_ok = choices.get("time_series") == "line" and choices.get("category") == "bar" and choices.get("composition") == "pie"
    checks.append({"name": "图表选择：时间、类别和组成", "passed": choices_ok})
    if not choices_ok:
        feedback.append("先判断数据形状：时间序列通常用 line，类别比较用 bar，构成比例才考虑 pie。")

    story_keys = {"question", "statistic", "chart_type", "count", "denominator", "observation", "boundary"}
    story_ok = story_keys.issubset(story) and story.get("chart_type") == "line" and story.get("count") == 7 and all(str(story.get(k, "")).strip() for k in ("question", "statistic", "denominator", "observation", "boundary"))
    checks.append({"name": "图表口径：问题、统计量、分母和图表类型", "passed": story_ok})
    if not story_ok:
        feedback.append("数据故事至少要说明问题、统计量、有效记录数/分母和图表类型。")

    boundary_text = str(story.get("boundary", ""))
    forbidden = ("一定导致", "证明所有人", "真实校园都", "因果关系成立")
    boundary_ok = bool(boundary_text.strip()) and not any(word in boundary_text for word in forbidden)
    checks.append({"name": "边界表达：模拟数据与因果限制", "passed": boundary_ok})
    if not boundary_ok:
        feedback.append("补充不能据此断言的内容；不要把模拟数据说成普遍规律，也不要把同时变化说成因果。")

    response_ok = changed.get("count") == 8 and changed.get("total") != base.get("total")
    checks.append({"name": "输入响应：增加一条记录后结果变化", "passed": response_ok})
    if not response_ok:
        feedback.append("检查是否把数据写死；增加一条记录后 count 和 total 应相应变化。")

    score = 25 * int(stats_ok) + 20 * int(choices_ok) + 20 * int(story_ok) + 20 * int(boundary_ok) + 15 * int(response_ok)
    return score, checks, feedback


def main() -> int:
    parser = argparse.ArgumentParser(description="U5 一页数据故事本地自动评分器")
    parser.add_argument("submission", type=Path)
    parser.add_argument("--json-result", type=Path)
    args = parser.parse_args()

    static_issues = static_check(args.submission)
    if static_issues:
        payload = {"score": 0, "checks": [], "feedback": static_issues + ["请先移除受限语法后再提交。"]}
    else:
        result, error = run_checks(args.submission)
        if error:
            payload = {"score": 0, "checks": [], "feedback": [error]}
        else:
            score, checks, feedback = grade(result or {})
            payload = {"score": score, "checks": checks, "feedback": feedback}

    print(f"U5 自动评分结果：{payload['score']}/100")
    for item in payload.get("checks", []):
        print(("通过" if item["passed"] else "未通过") + "｜" + item["name"])
    for item in payload.get("feedback", []):
        print("建议｜" + item)
    if args.json_result:
        args.json_result.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
