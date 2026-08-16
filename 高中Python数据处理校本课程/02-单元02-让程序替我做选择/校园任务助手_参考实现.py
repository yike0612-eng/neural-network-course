"""U2《让程序替我做选择》：校园任务助手参考实现。

用于教师演示与学生完成基础任务后的自检。
所有情境均为教学模拟；程序只提供建议，不替代人的最终判断。
"""


def suggest_activity(weather, free_minutes, task_done):
    """根据天气、时间和任务完成情况返回一条活动建议。"""
    if not task_done:
        return "先整理并完成当前任务；需要时可向同伴或老师求助。"
    elif free_minutes < 10:
        return "时间较短，建议喝水、整理物品或做短时放松。"
    elif weather == "雨":
        return "建议选择室内阅读、棋类或拉伸活动。"
    elif weather == "晴" and free_minutes >= 30:
        return "可以考虑户外运动或较完整的兴趣活动。"
    else:
        return "可以校园散步、阅读或进行短时兴趣活动。"


def run_test_cases(test_cases):
    """逐条运行模拟测试，并返回每条测试的输入和建议。"""
    results = []
    for test_case in test_cases:
        advice = suggest_activity(
            test_case["weather"],
            test_case["free_minutes"],
            test_case["task_done"],
        )
        results.append({"input": test_case, "advice": advice})
    return results


def count_indoor_advice(results):
    """统计含“室内”字样的建议数，用于选做练习。"""
    indoor_count = 0
    for result in results:
        if "室内" in result["advice"]:
            indoor_count += 1
    return indoor_count


# 教学模拟测试：含普通、边界与组合情形。
test_cases = [
    {"weather": "晴", "free_minutes": 5, "task_done": True},
    {"weather": "晴", "free_minutes": 10, "task_done": True},
    {"weather": "雨", "free_minutes": 20, "task_done": True},
    {"weather": "晴", "free_minutes": 30, "task_done": True},
    {"weather": "晴", "free_minutes": 30, "task_done": False},
    {"weather": "雨", "free_minutes": 5, "task_done": True},
]

results = run_test_cases(test_cases)

print("=" * 56)
print("校园任务助手：教学模拟测试结果")
print("=" * 56)
for number, result in enumerate(results, start=1):
    print(f"测试 {number}：{result['input']}")
    print(f"建议：{result['advice']}")
    print("-" * 56)

print(f"室内建议出现：{count_indoor_advice(results)} 次")
print("规则边界提醒：若输入未涵盖场地安全、学生意愿或真实需要，程序不应替人作最终决定。")
