"""汇总 U1《数据侦探的第一步》匿名随堂检测。

用法：
    python analyze_u1_quiz.py u1_quiz_responses_template.csv --output-dir quiz_report

输入文件每行只允许包含匿名 response_id 和 Q1—Q10 的 A/B/C/D 选项。
脚本仅输出班级与题目层面的汇总，不输出学生排名、单人分数或身份信息。
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


ANSWER_KEY = {
    "Q1": "B",
    "Q2": "B",
    "Q3": "C",
    "Q4": "A",
    "Q5": "A",
    "Q6": "D",
    "Q7": "A",
    "Q8": "B",
    "Q9": "C",
    "Q10": "A",
}

QUESTION_META = {
    "Q1": ("数据问题与结论边界", "区分可计算事实与因果/普遍结论"),
    "Q2": ("print() 输出", "区分代码文本与输出文本"),
    "Q3": ("变量与数据类型", "区分变量名、数值、文字与引号"),
    "Q4": ("条件边界", "理解 >= 包含相等情况"),
    "Q5": ("缩进与代码块", "理解缩进与条件/循环归属"),
    "Q6": ("循环累计", "追踪 total 在每一轮的变化"),
    "Q7": ("平均值", "将总量与天数对应计算"),
    "Q8": ("调试循环", "按现象、位置、最小修改、验证调试"),
    "Q9": ("IPO：处理", "区分输入、处理与输出"),
    "Q10": ("数据责任与结论边界", "用有限数据作有范围的解释"),
}

VALID_OPTIONS = {"A", "B", "C", "D"}


def priority_label(rate: float | None) -> str:
    if rate is None:
        return "未作答"
    if rate >= 0.80:
        return "稳定"
    if rate >= 0.60:
        return "需巩固"
    return "优先修订"


def percentage(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def format_rate(rate: float | None) -> str:
    return "—" if rate is None else f"{rate * 100:.1f}%"


def read_responses(input_path: Path) -> tuple[dict[str, Counter[str]], dict[str, int], int, int]:
    """读取选项，并在题目层面累计有效作答和无效作答。"""
    required_columns = ["response_id", *ANSWER_KEY]
    option_counts = {question: Counter() for question in ANSWER_KEY}
    invalid_counts = defaultdict(int)
    response_rows = 0
    rows_with_answer = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("输入 CSV 缺少表头。")

        missing = [column for column in required_columns if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"输入 CSV 缺少列：{', '.join(missing)}")

        for row in reader:
            response_rows += 1
            has_valid_answer = False
            for question in ANSWER_KEY:
                response = (row.get(question) or "").strip().upper()
                if not response:
                    continue
                if response not in VALID_OPTIONS:
                    invalid_counts[question] += 1
                    continue
                option_counts[question][response] += 1
                has_valid_answer = True
            if has_valid_answer:
                rows_with_answer += 1

    return option_counts, invalid_counts, response_rows, rows_with_answer


def write_question_summary(
    output_path: Path,
    option_counts: dict[str, Counter[str]],
    invalid_counts: dict[str, int],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "题号", "知识点", "正确答案", "有效作答数", "正确人数", "正确率",
                "A人数", "B人数", "C人数", "D人数", "无效作答数", "诊断标签", "优先检查",
            ],
        )
        writer.writeheader()
        for question, answer in ANSWER_KEY.items():
            knowledge, action = QUESTION_META[question]
            counts = option_counts[question]
            valid_answers = sum(counts.values())
            correct = counts[answer]
            rate = percentage(correct, valid_answers)
            row = {
                "题号": question,
                "知识点": knowledge,
                "正确答案": answer,
                "有效作答数": valid_answers,
                "正确人数": correct,
                "正确率": format_rate(rate),
                "A人数": counts["A"],
                "B人数": counts["B"],
                "C人数": counts["C"],
                "D人数": counts["D"],
                "无效作答数": invalid_counts[question],
                "诊断标签": priority_label(rate),
                "优先检查": action,
            }
            writer.writerow(row)
            rows.append(row)
    return rows


def write_knowledge_summary(output_path: Path, question_rows: list[dict[str, object]]) -> None:
    grouped: dict[str, dict[str, object]] = {}
    for row in question_rows:
        knowledge = str(row["知识点"])
        group = grouped.setdefault(
            knowledge,
            {"题号": [], "有效作答数": 0, "正确人数": 0, "优先检查": row["优先检查"]},
        )
        group["题号"].append(str(row["题号"]))
        group["有效作答数"] += int(row["有效作答数"])
        group["正确人数"] += int(row["正确人数"])

    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["知识点", "关联题号", "有效作答总数", "正确总数", "综合正确率", "诊断标签", "优先检查"],
        )
        writer.writeheader()
        for knowledge, group in grouped.items():
            rate = percentage(int(group["正确人数"]), int(group["有效作答数"]))
            writer.writerow(
                {
                    "知识点": knowledge,
                    "关联题号": "/".join(group["题号"]),
                    "有效作答总数": group["有效作答数"],
                    "正确总数": group["正确人数"],
                    "综合正确率": format_rate(rate),
                    "诊断标签": priority_label(rate),
                    "优先检查": group["优先检查"],
                }
            )


def write_markdown_report(
    output_path: Path,
    question_rows: list[dict[str, object]],
    response_rows: int,
    rows_with_answer: int,
) -> None:
    ranked = sorted(
        question_rows,
        key=lambda row: (
            2 if row["诊断标签"] == "优先修订" else 1 if row["诊断标签"] == "需巩固" else 0,
            float(str(row["正确率"]).rstrip("%")) if row["正确率"] != "—" else 101,
        ),
        reverse=True,
    )

    lines = [
        "# U1 随堂检测汇总报告",
        "",
        "## 使用边界",
        "",
        "本报告仅呈现班级与题目层面的匿名汇总，用于改进课堂资源；不包含学生姓名、单人得分或排名。题目正确率应与课堂观察、作品完成度和环境记录一起解释。",
        "",
        "## 数据完整性",
        "",
        f"- CSV 中共有 **{response_rows}** 行答卷记录。",
        f"- 其中至少有一题有效作答的匿名答卷为 **{rows_with_answer}** 份。",
        "- 空白或 A/B/C/D 以外的作答不会计入该题有效作答数。",
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

    lines.extend([
        "",
        "## 建议优先处理项",
        "",
    ])
    priorities = [row for row in ranked if row["诊断标签"] in {"优先修订", "需巩固"}]
    if not priorities:
        lines.append("当前没有出现需要优先处理的题目；仍请检查是否存在有效作答过少的题目。")
    else:
        for row in priorities[:3]:
            lines.append(
                f"- **{row['题号']}｜{row['知识点']}｜{row['诊断标签']}：** {row['优先检查']}"
            )

    lines.extend([
        "",
        "## 决策提醒",
        "",
        "不要仅凭选择题正确率决定是否进入 U2。优先选择一个同时得到课堂观察和作品证据支持的 P0 修订项；例如，当 Q6 循环累计正确率低且第 4 课大量学生无法解释 `total` 更新时，再优先补充循环手算追踪表。",
    ])
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="分析 U1 匿名随堂检测 CSV。")
    parser.add_argument("input_csv", type=Path, help="包含 response_id 和 Q1—Q10 的匿名答卷 CSV。")
    parser.add_argument("--output-dir", type=Path, default=Path("quiz_report"), help="汇总报告输出目录。")
    args = parser.parse_args()

    if not args.input_csv.is_file():
        parser.error(f"找不到输入文件：{args.input_csv}")

    try:
        option_counts, invalid_counts, response_rows, rows_with_answer = read_responses(args.input_csv)
    except ValueError as error:
        parser.error(str(error))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    question_rows = write_question_summary(
        args.output_dir / "U1题目汇总.csv", option_counts, invalid_counts
    )
    write_knowledge_summary(args.output_dir / "U1知识点汇总.csv", question_rows)
    write_markdown_report(
        args.output_dir / "U1随堂检测汇总报告.md",
        question_rows,
        response_rows,
        rows_with_answer,
    )

    print("已生成匿名班级汇总：")
    print(args.output_dir / "U1随堂检测汇总报告.md")
    print(args.output_dir / "U1题目汇总.csv")
    print(args.output_dir / "U1知识点汇总.csv")
    if rows_with_answer == 0:
        print("提醒：当前没有有效作答；请录入匿名选项后再解读报告。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
