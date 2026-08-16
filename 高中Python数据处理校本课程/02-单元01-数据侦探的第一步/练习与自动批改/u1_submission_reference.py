"""U1 自动批改参考提交文件。

只包含函数定义，可用 grade_u1.py 进行核验。
"""


def format_goal(topic, goal, unit):
    return f"主题：{topic}｜每日目标：{goal}{unit}"


def daily_status(minutes, goal):
    if minutes >= goal:
        return "达标"
    return "未达标"


def weekly_summary(records, goal):
    if len(records) == 0:
        return {"total": 0, "average": 0, "goal_days": 0}

    total = 0
    goal_days = 0

    for minutes in records:
        total += minutes
        if minutes >= goal:
            goal_days += 1

    average = total / len(records)
    return {"total": total, "average": average, "goal_days": goal_days}


def longest_goal_streak(records, goal):
    current_streak = 0
    longest_streak = 0

    for minutes in records:
        if minutes >= goal:
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
        else:
            current_streak = 0

    return longest_streak
