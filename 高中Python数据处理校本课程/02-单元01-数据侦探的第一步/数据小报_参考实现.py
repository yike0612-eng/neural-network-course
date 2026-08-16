"""U1《数据侦探的第一步》：周数据小报参考实现

适用：教师演示、学生提交后的自检。
数据为教学模拟数据；请勿用本程序收集或保存敏感个人信息。
"""


def count_goal_days(records, goal):
    """返回达到目标的天数。"""
    goal_days = 0
    for value in records:
        if value >= goal:
            goal_days += 1
    return goal_days


def longest_goal_streak(records, goal):
    """挑战任务：返回连续达标的最长天数。"""
    current_streak = 0
    longest_streak = 0

    for value in records:
        if value >= goal:
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
        else:
            current_streak = 0

    return longest_streak


def create_week_report(topic, unit, records, daily_goal):
    """根据一周记录打印一份数据小报。"""
    if len(records) == 0:
        print("没有可处理的数据，请先提供至少一条记录。")
        return

    total_value = sum(records)
    average_value = total_value / len(records)
    goal_days = count_goal_days(records, daily_goal)
    longest_streak = longest_goal_streak(records, daily_goal)

    print("=" * 40)
    print(f"{topic}周数据小报")
    print("=" * 40)
    print(f"每日目标：{daily_goal} {unit}")
    print("-" * 40)

    for day_number, value in enumerate(records, start=1):
        if value >= daily_goal:
            status = "达标"
        else:
            status = "未达标"
        print(f"第 {day_number} 天：{value:>3} {unit}  |  {status}")

    print("-" * 40)
    print(f"本周总{topic}量：{total_value} {unit}")
    print(f"平均每天：{average_value:.1f} {unit}")
    print(f"达标天数：{goal_days} 天 / {len(records)} 天")
    print(f"最长连续达标：{longest_streak} 天")

    if goal_days >= 5:
        print("建议：你的节奏比较稳定，可以尝试保持这个习惯。")
    elif goal_days >= 3:
        print("建议：你已经有一定基础，可以分析未达标日的原因并设置提醒。")
    else:
        print("建议：可以从一个更容易坚持的小目标开始，例如每天增加 5 分钟。")

    print("=" * 40)
    print("数据边界提醒：这份结果只描述当前 7 条记录，不能据此推断长期习惯、因果关系或他人的情况。")


# 教学模拟数据：可按课堂需要更改数值或主题。
topic = "阅读"
unit = "分钟"
weekly_minutes = [25, 35, 40, 15, 30, 50, 20]
daily_goal = 30

create_week_report(topic, unit, weekly_minutes, daily_goal)
