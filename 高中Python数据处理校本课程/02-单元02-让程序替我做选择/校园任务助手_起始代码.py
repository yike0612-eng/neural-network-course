"""U2《让程序替我做选择》：校园任务助手起始代码。

本程序使用教学模拟情境，不收集或保存任何真实学生的敏感个人信息。
先完成函数中的 TODO，再运行文件末尾的测试情境。
"""


def suggest_activity(weather, free_minutes, task_done):
    """根据模拟情境返回一条建议。"""
    if not task_done:
        return "先整理并完成当前任务；需要时可向同伴或老师求助。"

    # TODO 1：当时间短于 10 分钟时，返回短时活动建议。
    # elif ______________________________:
    #     return "时间较短，建议喝水、整理物品或做短时放松。"

    # TODO 2：当雨天且有足够时间时，返回室内活动建议。
    # elif ______________________________:
    #     return "建议选择室内阅读、棋类或拉伸活动。"

    # TODO 3：当天气晴、时间不少于 30 分钟时，返回户外活动建议。
    # elif ______________________________:
    #     return "可以考虑户外运动或较完整的兴趣活动。"

    return "可以校园散步、阅读或进行短时兴趣活动。"


situations = [
    {"weather": "晴", "free_minutes": 5, "task_done": True},
    {"weather": "雨", "free_minutes": 20, "task_done": True},
    {"weather": "晴", "free_minutes": 30, "task_done": False},
    {"weather": "晴", "free_minutes": 30, "task_done": True},
]

print("=" * 44)
print("校园任务助手：教学模拟测试")
print("=" * 44)

for number, situation in enumerate(situations, start=1):
    advice = suggest_activity(
        situation["weather"],
        situation["free_minutes"],
        situation["task_done"],
    )
    print(f"情境 {number}：{situation}")
    print(f"建议：{advice}")
    print("-" * 44)

print("提醒：程序只能按给定规则提供建议；真实情境仍需由人结合安全、意愿和实际条件判断。")
