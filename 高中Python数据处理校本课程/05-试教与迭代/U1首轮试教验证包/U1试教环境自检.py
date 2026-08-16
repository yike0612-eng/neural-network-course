"""U1《数据侦探的第一步》首轮试教环境自检。

在本文件所在目录运行：
    python U1试教环境自检.py

本脚本只检查本地课程资源、Python 版本、示例代码与自动批改参考提交是否可用；
不会联网、不会读取学生作品，也不会收集任何个人信息。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


COURSE_ROOT = Path(__file__).resolve().parents[2]
U1_ROOT = COURSE_ROOT / "02-单元01-数据侦探的第一步"
AUTOGRADER_ROOT = U1_ROOT / "练习与自动批改"

REQUIRED_FILES = {
    "教师指导书": U1_ROOT / "教师指导书-v1.md",
    "学生学习单": U1_ROOT / "学生学习单-v1.md",
    "单元评价量规": U1_ROOT / "单元评价量规-v1.md",
    "调试卡": U1_ROOT / "调试卡-v1.md",
    "起始代码": U1_ROOT / "数据小报_起始代码.py",
    "参考实现": U1_ROOT / "数据小报_参考实现.py",
    "自动批改器": AUTOGRADER_ROOT / "grade_u1.py",
    "自动批改模板": AUTOGRADER_ROOT / "u1_submission_template.py",
    "自动批改参考提交": AUTOGRADER_ROOT / "u1_submission_reference.py",
}


def run_program(label: str, command: list[str]) -> bool:
    """以短超时运行一个本地命令，并输出适合教师判断的结果。"""
    try:
        completed = subprocess.run(
            command,
            cwd=COURSE_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"[未通过] {label}：运行超过 8 秒。")
        return False

    if completed.returncode == 0:
        print(f"[通过] {label}")
        return True

    detail = completed.stderr.strip() or completed.stdout.strip() or "未返回错误信息"
    print(f"[未通过] {label}：{detail}")
    return False


def main() -> int:
    print("=" * 60)
    print("U1《数据侦探的第一步》首轮试教环境自检")
    print(f"课程根目录：{COURSE_ROOT}")
    print("=" * 60)

    checks: list[bool] = []

    python_ok = sys.version_info >= (3, 10)
    version = ".".join(str(value) for value in sys.version_info[:3])
    if python_ok:
        print(f"[通过] Python 版本：{version}")
    else:
        print(f"[未通过] Python 版本：{version}；本课程建议使用 Python 3.10+。")
    checks.append(python_ok)

    for label, path in REQUIRED_FILES.items():
        exists = path.is_file()
        state = "通过" if exists else "未通过"
        print(f"[{state}] {label}：{path.relative_to(COURSE_ROOT)}")
        checks.append(exists)

    if not all(checks):
        print("-" * 60)
        print("资源不完整；请先补齐未通过项目，再运行本脚本。")
        return 1

    checks.append(
        run_program(
            "U1 起始代码语法检查",
            [sys.executable, "-m", "py_compile", str(REQUIRED_FILES["起始代码"])],
        )
    )
    checks.append(
        run_program(
            "U1 参考实现运行",
            [sys.executable, str(REQUIRED_FILES["参考实现"])],
        )
    )
    checks.append(
        run_program(
            "U1 自动批改参考回归",
            [
                sys.executable,
                str(REQUIRED_FILES["自动批改器"]),
                str(REQUIRED_FILES["自动批改参考提交"]),
            ],
        )
    )

    print("-" * 60)
    passed = sum(checks)
    total = len(checks)
    print(f"自检汇总：{passed}/{total} 项通过")
    if all(checks):
        print("环境与资源链路已就绪。试教前仍应在每间机房随机抽检 3 台学生机。")
        return 0

    print("请先解决未通过项目；未达到全通过时，不建议启动正式试教。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
