"""U1《数据侦探的第一步》本地自动批改器。

用法：python grade_u1.py u1_submission.py

说明：本工具用于受控课堂中的初学者练习。它不是安全沙箱；不要执行来自
互联网或身份不明来源的代码，也不要在存放敏感资料的教师电脑上直接批改。
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path


REQUIRED_FUNCTIONS = {
    "format_goal": "请保留 format_goal(topic, goal, unit) 这个函数名。",
    "daily_status": "请保留 daily_status(minutes, goal) 这个函数名。",
    "weekly_summary": "请保留 weekly_summary(records, goal) 这个函数名。",
}
OPTIONAL_FUNCTIONS = {"longest_goal_streak"}
ALLOWED_FUNCTIONS = set(REQUIRED_FUNCTIONS) | OPTIONAL_FUNCTIONS
ALLOWED_CALLS = {"len", "sum", "range", "round", "int", "float", "str"}
MAX_SOURCE_CHARS = 15_000
TIMEOUT_SECONDS = 3


class SafeSubsetChecker(ast.NodeVisitor):
    """检查提交代码是否处于本练习所需的、有限的语法子集内。"""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, node: ast.AST, message: str) -> None:
        self.errors.append(f"第 {getattr(node, 'lineno', '?')} 行：{message}")

    def visit_Import(self, node: ast.Import) -> None:
        self.error(node, "提交文件不允许 import；展示版程序请另存文件。")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.error(node, "提交文件不允许 import；展示版程序请另存文件。")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.error(node, "本练习不允许对象属性调用或访问，请只使用基础变量、列表和函数。")

    def visit_While(self, node: ast.While) -> None:
        self.error(node, "本练习优先使用 for 循环；请不要使用 while 循环。")

    def visit_With(self, node: ast.With) -> None:
        self.error(node, "提交文件不允许文件或环境操作。")

    def visit_Try(self, node: ast.Try) -> None:
        self.error(node, "本练习暂不需要异常处理；请先完成基础逻辑。")

    def visit_Raise(self, node: ast.Raise) -> None:
        self.error(node, "提交文件不允许主动抛出异常。")

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.error(node, "本练习不使用 lambda，请写清楚的函数定义。")

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用列表推导式。")

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用集合推导式。")

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用字典推导式。")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.error(node, "本练习不使用生成器表达式。")

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_CALLS:
            self.error(
                node,
                "提交文件只允许调用 len、sum、range、round、int、float、str；"
                "不要写 input、print、open 或其他调用。",
            )
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self.error(node, "本练习不需要 global。")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.error(node, "本练习不需要 nonlocal。")

    def visit_Delete(self, node: ast.Delete) -> None:
        self.error(node, "提交文件不允许删除变量或数据。")


def is_docstring(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def validate_structure(tree: ast.Module) -> list[str]:
    """限制顶层只有文档字符串和指定的函数定义。"""
    errors: list[str] = []
    found: set[str] = set()

    for index, node in enumerate(tree.body):
        if is_docstring(node) and index == 0:
            continue
        if not isinstance(node, ast.FunctionDef):
            errors.append(
                f"第 {getattr(node, 'lineno', '?')} 行：提交文件只能包含函数定义；"
                "请把展示用 print() 或 input() 放到另一个文件。"
            )
            continue
        if node.name not in ALLOWED_FUNCTIONS:
            errors.append(f"第 {node.lineno} 行：不需要额外函数 {node.name!r}，请先完成规定接口。")
        if node.name in found:
            errors.append(f"第 {node.lineno} 行：函数 {node.name!r} 被重复定义。")
        found.add(node.name)
        if node.decorator_list:
            errors.append(f"第 {node.lineno} 行：本练习不使用装饰器。")
        if node.returns is not None or any(arg.annotation is not None for arg in node.args.args):
            errors.append(f"第 {node.lineno} 行：本练习不需要类型标注，请保持函数头简洁。")
        if node.args.defaults or node.args.kw_defaults:
            errors.append(f"第 {node.lineno} 行：本练习不使用默认参数。")

    for name, message in REQUIRED_FUNCTIONS.items():
        if name not in found:
            errors.append(message)
    return errors


def static_check(path: Path) -> list[str]:
    if not path.exists():
        return [f"未找到提交文件：{path}"]
    if path.suffix != ".py":
        return ["提交文件必须是 .py 文件。"]

    source = path.read_text(encoding="utf-8")
    if len(source) > MAX_SOURCE_CHARS:
        return [f"提交文件超过 {MAX_SOURCE_CHARS} 个字符；请只保留本练习的函数定义。"]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [f"语法错误：第 {error.lineno} 行 {error.msg}"]

    errors = validate_structure(tree)
    checker = SafeSubsetChecker()
    checker.visit(tree)
    errors.extend(checker.errors)
    return errors


WORKER_CODE = r'''
import importlib.util
import json
import math
import sys

submission_path = sys.argv[1]
results = []


def add(name, passed, message):
    results.append({"name": name, "passed": bool(passed), "message": message})


def load_submission():
    spec = importlib.util.spec_from_file_location("u1_submission", submission_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(module, function_name, args):
    function = getattr(module, function_name)
    return function(*args)


def test_equal(module, name, function_name, args, expected, hint):
    try:
        actual = call(module, function_name, args)
        if actual == expected:
            add(name, True, "通过")
        else:
            add(name, False, f"期望返回 {expected!r}，实际得到 {actual!r}。{hint}")
    except Exception as error:
        add(name, False, f"运行时出现 {type(error).__name__}: {error}。{hint}")


def test_summary(module, name, records, goal, expected, hint):
    try:
        actual = call(module, "weekly_summary", (records, goal))
        if not isinstance(actual, dict):
            add(name, False, f"weekly_summary 应返回字典，实际得到 {type(actual).__name__}。{hint}")
            return
        expected_keys = {"total", "average", "goal_days"}
        if set(actual) != expected_keys:
            add(name, False, f"字典键应为 {sorted(expected_keys)!r}，实际得到 {sorted(actual)!r}。{hint}")
            return
        total_ok = actual["total"] == expected["total"]
        average_ok = isinstance(actual["average"], (int, float)) and math.isclose(
            actual["average"], expected["average"], rel_tol=1e-9, abs_tol=1e-9
        )
        goal_days_ok = actual["goal_days"] == expected["goal_days"]
        if total_ok and average_ok and goal_days_ok:
            add(name, True, "通过")
        else:
            add(
                name,
                False,
                f"期望 {expected!r}，实际得到 {actual!r}。{hint}",
            )
    except Exception as error:
        add(name, False, f"运行时出现 {type(error).__name__}: {error}。{hint}")


try:
    module = load_submission()
except Exception as error:
    add("导入提交文件", False, f"无法导入：{type(error).__name__}: {error}")
    print(json.dumps({"results": results}, ensure_ascii=False))
    raise SystemExit(0)

# E1：变量与格式化
# 为避免格式偏好造成误判，先要求学生使用规定输出格式。
test_equal(
    module,
    "E1-1 目标文本",
    "format_goal",
    ("阅读", 30, "分钟"),
    "主题：阅读｜每日目标：30分钟",
    "检查 f-string 或字符串拼接，注意中文标点和变量顺序。",
)
test_equal(
    module,
    "E1-2 更换主题",
    "format_goal",
    ("运动", 45, "分钟"),
    "主题：运动｜每日目标：45分钟",
    "不要把主题或目标写死在函数里。",
)

# E2：条件与边界
test_equal(
    module,
    "E2-1 边界值判定",
    "daily_status",
    (30, 30),
    "达标",
    "达到目标也应判为达标，请检查 >= 是否写成了 >。",
)
test_equal(
    module,
    "E2-2 未达标判定",
    "daily_status",
    (29, 30),
    "未达标",
    "检查 if / else 的两个返回值是否完整。",
)
test_equal(
    module,
    "E2-3 超过目标判定",
    "daily_status",
    (45, 30),
    "达标",
    "不要只判断相等；超过目标也应达标。",
)

# E3：循环与汇总
test_summary(
    module,
    "E3-1 一周汇总",
    [25, 35, 40, 15, 30, 50, 20],
    30,
    {"total": 215, "average": 215 / 7, "goal_days": 4},
    "检查循环中的累计、目标判断与平均值计算。",
)
test_summary(
    module,
    "E3-2 边界与计数",
    [30, 29, 31],
    30,
    {"total": 90, "average": 30, "goal_days": 2},
    "目标值本身也应计入达标天数。",
)
test_summary(
    module,
    "E3-3 空列表",
    [],
    30,
    {"total": 0, "average": 0, "goal_days": 0},
    "先判断 records 是否为空，避免除以 0。",
)

# E4：挑战题；未实现不计入基础通过数。
if hasattr(module, "longest_goal_streak"):
    test_equal(
        module,
        "E4 挑战：最长连续达标",
        "longest_goal_streak",
        ([30, 31, 20, 32, 33], 30),
        2,
        "达标时累加连续天数，未达标时清零，并保存历史最大值。",
    )

print(json.dumps({"results": results}, ensure_ascii=False))
'''


def run_tests(path: Path) -> tuple[list[dict[str, object]], str | None]:
    """在受超时控制的独立 Python 进程中运行行为测试。"""
    with tempfile.TemporaryDirectory(prefix="u1_grade_") as temp_dir:
        worker_path = Path(temp_dir) / "worker.py"
        worker_path.write_text(textwrap.dedent(WORKER_CODE), encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(worker_path), str(path.resolve())],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return [], f"运行超过 {TIMEOUT_SECONDS} 秒，可能存在过长循环或未完成的逻辑。"

    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
        results = payload["results"]
        if not isinstance(results, list):
            raise ValueError("results 不是列表")
        return results, None
    except (IndexError, json.JSONDecodeError, KeyError, ValueError) as error:
        detail = completed.stderr.strip() or completed.stdout.strip() or str(error)
        return [], f"批改器没有得到有效结果：{detail}"


def print_header(path: Path) -> None:
    print("=" * 60)
    print("U1《数据侦探的第一步》自动批改结果")
    print(f"提交文件：{path.name}")
    print("=" * 60)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python grade_u1.py u1_submission.py")
        return 2

    submission_path = Path(sys.argv[1])
    print_header(submission_path)

    errors = static_check(submission_path)
    if errors:
        print("提交文件暂不能进入行为测试，请先完成以下修改：")
        for error in errors:
            print(f"- {error}")
        return 1

    results, infrastructure_error = run_tests(submission_path)
    if infrastructure_error:
        print(f"批改中断：{infrastructure_error}")
        return 1

    core_results = [result for result in results if not str(result["name"]).startswith("E4")]
    passed_core = sum(bool(result["passed"]) for result in core_results)

    for result in results:
        icon = "通过" if result["passed"] else "未通过"
        print(f"[{icon}] {result['name']}：{result['message']}")

    print("-" * 60)
    print(f"基础任务通过：{passed_core}/{len(core_results)}")
    if passed_core == len(core_results):
        print("很好。基础逻辑已通过，请把精力放到周数据小报的可读性、IPO 图与数据边界反思。")
        return 0
    print("建议：优先修改第一条“未通过”反馈，再次运行批改器；不要一次同时改很多地方。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
