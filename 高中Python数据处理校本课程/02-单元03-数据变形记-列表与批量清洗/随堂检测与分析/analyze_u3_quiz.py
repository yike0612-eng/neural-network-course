"""Aggregate anonymous multiple-choice quiz responses without student ranking.

Usage:
    python analyze_anonymous_quiz.py responses.csv quiz_config.json --output-dir report

The config file defines question IDs, answer keys, knowledge tags, and review prompts.
The script writes only class- and question-level summaries; it never writes individual scores.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

VALID_OPTIONS = {"A", "B", "C", "D"}


def rate(correct: int, attempts: int) -> float | None:
    return None if attempts == 0 else correct / attempts


def show_rate(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def label(value: float | None, stable: float, review: float) -> str:
    if value is None:
        return "未作答"
    if value >= stable:
        return "稳定"
    if value >= review:
        return "需巩固"
    return "优先修订"


def load_config(path: Path) -> tuple[list[dict[str, str]], float, float]:
    config = json.loads(path.read_text(encoding="utf-8"))
    questions = config.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("配置文件必须包含非空 questions 列表。")

    required = {"id", "answer", "knowledge", "review_prompt"}
    for item in questions:
        if not required.issubset(item):
            raise ValueError(f"题目配置缺少字段：{required - set(item)}")
        if str(item["answer"]).upper() not in VALID_OPTIONS:
            raise ValueError(f"题目 {item['id']} 的正确选项必须是 A/B/C/D。")

    stable = float(config.get("stable_threshold", 0.80))
    review = float(config.get("review_threshold", 0.60))
    if not 0 <= review <= stable <= 1:
        raise ValueError("阈值应满足 0 <= review_threshold <= stable_threshold <= 1。")
    return questions, stable, review


def read_csv(path: Path, question_ids: list[str]) -> tuple[dict[str, Counter[str]], dict[str, int], int, int]:
    counters = {qid: Counter() for qid in question_ids}
    invalid = defaultdict(int)
    row_count = 0
    active_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["response_id", *question_ids]
        if reader.fieldnames is None:
            raise ValueError("答卷 CSV 缺少表头。")
        missing = [name for name in expected if name not in reader.fieldnames]
        if missing:
            raise ValueError("答卷 CSV 缺少列：" + ", ".join(missing))

        for row in reader:
            row_count += 1
            has_answer = False
            for qid in question_ids:
                choice = (row.get(qid) or "").strip().upper()
                if not choice:
                    continue
                if choice not in VALID_OPTIONS:
                    invalid[qid] += 1
                    continue
                counters[qid][choice] += 1
                has_answer = True
            if has_answer:
                active_rows += 1
    return counters, invalid, row_count, active_rows


def write_outputs(
    output_dir: Path,
    questions: list[dict[str, str]],
    counters: dict[str, Counter[str]],
    invalid: dict[str, int],
    row_count: int,
    active_rows: int,
    stable: float,
    review: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    question_rows: list[dict[str, str | int]] = []
    for item in questions:
        qid = str(item["id"])
        counts = counters[qid]
        attempts = sum(counts.values())
        correct = counts[str(item["answer"]).upper()]
        current_rate = rate(correct, attempts)
        question_rows.append({
            "题号": qid,
            "知识点": str(item["knowledge"]),
            "正确答案": str(item["answer"]).upper(),
            "有效作答数": attempts,
            "正确人数": correct,
            "正确率": show_rate(current_rate),
            "A人数": counts["A"],
            "B人数": counts["B"],
            "C人数": counts["C"],
            "D人数": counts["D"],
            "无效作答数": invalid.get(qid, 0),
            "诊断标签": label(current_rate, stable, review),
            "优先检查": str(item["review_prompt"]),
        })

    question_file = output_dir / "题目汇总.csv"
    with question_file.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(question_rows[0]))
        writer.writeheader()
        writer.writerows(question_rows)

    groups: dict[str, dict[str, object]] = {}
    for row in question_rows:
        group = groups.setdefault(
            str(row["知识点"]),
            {"题号": [], "attempts": 0, "correct": 0, "prompt": row["优先检查"]},
        )
        group["题号"].append(str(row["题号"]))
        group["attempts"] += int(row["有效作答数"])
        group["correct"] += int(row["正确人数"])

    knowledge_rows = []
    for knowledge, group in groups.items():
        current_rate = rate(int(group["correct"]), int(group["attempts"]))
        knowledge_rows.append({
            "知识点": knowledge,
            "关联题号": "/".join(group["题号"]),
            "有效作答总数": group["attempts"],
            "正确总数": group["correct"],
            "综合正确率": show_rate(current_rate),
            "诊断标签": label(current_rate, stable, review),
            "优先检查": group["prompt"],
        })

    knowledge_file = output_dir / "知识点汇总.csv"
    with knowledge_file.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(knowledge_rows[0]))
        writer.writeheader()
        writer.writerows(knowledge_rows)

    lines = [
        "# 匿名随堂检测汇总报告",
        "",
        "本报告只呈现班级与题目层面的汇总，不输出个人分数、排名或身份信息。请将题目结果与课堂观察、作品完成度和环境记录一起解释。",
        "",
        "## 数据完整性",
        "",
        f"- CSV 中共有 **{row_count}** 行答卷记录。",
        f"- 其中至少有一题有效作答的匿名答卷为 **{active_rows}** 份。",
        "",
        "## 题目汇总",
        "",
        "| 题号 | 知识点 | 有效作答 | 正确率 | 诊断 | 优先检查 |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in question_rows:
        lines.append(
            f"| {row['题号']} | {row['知识点']} | {row['有效作答数']} | {row['正确率']} | {row['诊断标签']} | {row['优先检查']} |"
        )

    candidates = [row for row in question_rows if row["诊断标签"] in {"优先修订", "需巩固"}]
    lines.extend(["", "## 复盘建议", ""])
    if candidates:
        priority_order = {"优先修订": 0, "需巩固": 1}
        candidates.sort(key=lambda row: (priority_order[str(row["诊断标签"])], str(row["正确率"])))
        for row in candidates[:3]:
            lines.append(f"- **{row['题号']}｜{row['知识点']}｜{row['诊断标签']}：** {row['优先检查']}")
    else:
        lines.append("当前没有出现需要优先处理的题目；仍请检查有效作答数量是否足够。")
    (output_dir / "匿名随堂检测汇总报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="汇总匿名选择题结果，不输出学生排名。")
    parser.add_argument("responses_csv", type=Path)
    parser.add_argument("config_json", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("quiz_report"))
    args = parser.parse_args()

    if not args.responses_csv.is_file() or not args.config_json.is_file():
        parser.error("答卷 CSV 或配置 JSON 不存在。")
    try:
        questions, stable, review = load_config(args.config_json)
        question_ids = [str(item["id"]) for item in questions]
        counters, invalid, row_count, active_rows = read_csv(args.responses_csv, question_ids)
    except (ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))

    write_outputs(args.output_dir, questions, counters, invalid, row_count, active_rows, stable, review)
    print(f"已生成班级匿名汇总：{args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
