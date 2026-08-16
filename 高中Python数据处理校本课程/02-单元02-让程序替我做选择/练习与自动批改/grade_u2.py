"""U2《让程序替我做选择》本地自动批改器。

用法：python grade_u2.py u2_submission.py

本工具仅用于受控课堂内的初学者练习反馈，不是安全沙箱。不要执行来自
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
    "is_short_time": "请保留 is_short_time(free_minutes) 这个函数名。",
    "basic_advice": "请保留 basic_advice(free_minutes, task_done) 这个函数名。",
    "suggest_activity": "请保留 suggest_activity(weather, free_minutes, task_done) 这个函数名。",
    "batch_advice": "请保留 batch_advice(situations) 这个函数名。",
}
OPTIONAL_FUNCTIONS = {"count_indoor_advice"}
ALLOWED_FUNCTIONS = set(REQUIRED_FUNCTIONS) | OPTIONAL_FUNCTIONS
ALLOWED_CALLS = {"len", "range"} | ALLOWED_FUNCTIONS
MAX_SOURCE_CHARS = 18_000
TIMEOUT_SECONDS = 3


class SafeSubsetChecker(ast.NodeVisitor):
    """检查提交是否只使用U2所需的有限语法。"""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, node: ast.AST, message: str) -> None:
        self.errors.append(f"第 {getattr(node, 'lineno', '?')} 行：{message}")

    def visit_Import(self, node: ast.Import) -> None:
        self.error(node, "提交文件不允许 import；展示代码请另存文件。")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.error(node, "提交文件不允许 import；展示代码请另存文件。")

    def visit_While(self, node: ast.While) -> None:
        self.error(node, "本练习优先使用 for 循环；请不要使用 while。")

    def visit_With(self, node: ast.With) -> None:
        self.error(node, "提交文件不允许文件或环境操作。")

    def visit_Try(self, node: ast.Try) -> None:
        self.error(node, "本练习暂不需要异常处理；请先完成基础规则。")

    def visit_Raise(self, node: ast.Raise) -> None:
        self.error(node, "提交文件不允许主动抛出异常。")

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.error(node, "本练习请使用普通函数定义。")

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用列表推导式。")

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用集合推导式。")

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.error(node, "本练习请用 for 循环，不使用字典推导式。")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.error(node, "本练习不使用生成器表达式。")

    def visit_Global(self, node: ast.Global) -> None:
        self.error(node, "本练习不需要 global。")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.error(node, "本练习不需要 nonlocal。")

    def visit_Delete(self, node: ast.Delete) -> None:
        self.error(node, "提交文件不允许删除变量或数据。")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.error(node, "本练习仅允许在列表变量上使用 append()；不要使用其他属性访问。")

    def visit_Call(self, node: ast.Call) -> None:
        allowed = False
        if isinstance(node.func, ast.Name) and node.func.id in ALLOWED_CALLS:
            allowed = True
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "append"
            and isinstance(node.func.value, ast.Name)
        ):
            allowed = True

        if not allowed:
            self.error(
                node,
                "提交文件只允许调用 len、range、规定函数和列表 append()；"
                "不要写 input、print、open 或其他调用。",
            )

        # 手动访问参数，避免把允许的 .append 当成一般属性访问。
        for argument in node.args:
            self.visit(argument)
        for keyword in node.keywords:
            self.visit(keyword.value)


def is_docstring(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def validate_structure(tree: ast.Module) -> list[str]:
    errors: list[str] = []
    found: set[str] = set()

    for index, node in enumerate(tree.body):
        if is_docstring(node) and index == 0:
            continue
        if not isinstance(node, ast.FunctionDef):
            errors.append(
                f"第 {getattr(node, 'lineno', '?')} 行：提交文件只能包含函数定义；"
                "请把 print() 和展示代码放到另一个文件。"
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
            errors.append(f"第 {node.lineno} 行：本练习不需要类型标注。")
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
import copy
import importlib.util
import json
import sys

submission_path = sys.argv[1]
results = []


def add(name, passed, message):
    results.append({"name": name, "passed": bool(passed), "message": message})


def load_submission():
    spec = importlib.util.spec_from_file_location("u2_submission", submission_path)
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


def test_batch(module):
    situations = [
        {"weather": "晴", "free_minutes": 5, "task_done": True},
        {"weather": "雨", "free_minutes": 20, "task_done": True},
        {"weather": "晴", "free_minutes": 30, "task_done": False},
    ]
    original = copy.deepcopy(situations)
    expected = ["短时整理", "室内活动", "完成任务"]
    try:
        actual = call(module, "batch_advice", (situations,))
        if actual != expected:
            add(
                "E4-1 批量建议",
                False,
                f"期望 {expected!r}，实际得到 {actual!r}。检查是否逐条调用 suggest_activity 并按顺序加入列表。",
            )
        elif situations != original:
            add(
                "E4-1 批量建议",
                False,
                "输出正确，但修改了原始 situations 列表。请新建结果列表，不要改写输入数据。",
            )
        else:
            add("E4-1 批量建议", True, "通过")
    except Exception as error:
        add("E4-1 批量建议", False, f"运行时出现 {type(error).__name__}: {error}。检查循环和 append()。")


try:
    module = load_submission()
except Exception as error:
    add("导入提交文件", False, f"无法导入：{type(error).__name__}: {error}")
    print(json.dumps({"results": results}, ensure_ascii=False))
    raise SystemExit(0)

# E1：布尔边界
test_equal(module, "E1-1 9分钟是短时", "is_short_time", (9,), True, "少于 10 分钟应返回 True。")
test_equal(module, "E1-2 10分钟不是短时", "is_short_time", (10,), False, "10 分钟是边界；检查 < 是否误写成 <=。")
test_equal(module, "E1-3 11分钟不是短时", "is_short_time", (11,), False, "检查比较表达式是否返回布尔值。")

# E2：基础优先级
test_equal(module, "E2-1 未完成任务优先", "basic_advice", (5, False), "完成任务", "任务未完成时应优先于时间短。")
test_equal(module, "E2-2 短时整理", "basic_advice", (5, True), "短时整理", "完成任务后，少于 10 分钟应返回“短时整理”。")
test_equal(module, "E2-3 一般情形", "basic_advice", (10, True), "自由安排", "10 分钟不属于短时；检查边界。")

# E3：多分支助手
test_equal(module, "E3-1 雨天室内", "suggest_activity", ("雨", 20, True), "室内活动", "雨天且时间不短时应返回“室内活动”。")
test_equal(module, "E3-2 晴天户外", "suggest_activity", ("晴", 30, True), "户外活动", "晴天且不少于 30 分钟时应返回“户外活动”。")
test_equal(module, "E3-3 组合边界", "suggest_activity", ("雨", 5, True), "短时整理", "本练习规定时间短优先于雨天；检查 elif 顺序。")
test_equal(module, "E3-4 任务优先", "suggest_activity", ("晴", 30, False), "完成任务", "任务未完成应优先于其他条件。")
test_equal(module, "E3-5 默认分支", "suggest_activity", ("晴", 10, True), "自由安排", "检查 else 是否覆盖一般情形。")

# E4：批量处理
test_batch(module)

# E5：可选挑战
if hasattr(module, "count_indoor_advice"):
    test_equal(
        module,
        "E5 挑战：室内建议计数",
        "count_indoor_advice",
        (["室内活动", "短时整理", "室内活动"],),
        2,
        "用循环逐项检查是否等于“室内活动”。",
    )

print(json.dumps({"results": results}, ensure_ascii=False))
'''


def run_tests(path: Path) -> tuple[list[dict[str, object]], str | None]:
    with tempfile.TemporaryDirectory(prefix="u2_grade_") as temp_dir:
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


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python grade_u2.py u2_submission.py")
        return 2

    submission_path = Path(sys.argv[1])
    print("=" * 60)
    print("U2《让程序替我做选择》自动批改结果")
    print(f"提交文件：{submission_path.name}")
    print("=" * 60)

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

    core_results = [result for result in results if not str(result["name"]).startswith("E5")]
    passed_core = sum(bool(result["passed"]) for result in core_results)

    for result in results:
        state = "通过" if result["passed"] else "未通过"
        print(f"[{state}] {result['name']}：{result['message']}")

    print("-" * 60)
    print(f"基础任务通过：{passed_core}/{len(core_results)}")
    if passed_core == len(core_results):
        print("很好。基础规则已通过，请继续完善流程图、边界反思和展示版程序。")
        return 0
    print("建议：优先根据第一条“未通过”反馈做最小修改，再次运行批改器。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
