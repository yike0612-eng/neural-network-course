"""U1 自动批改提交模板。

只保留函数定义，不要写 input()、文件读写、import 或顶层测试代码。
展示用的周数据小报请另存为 week_report.py。
"""


def format_goal(topic, goal, unit):
    """返回目标说明，例如：主题：阅读｜每日目标：30分钟。"""
    # TODO：用变量和 f-string（或字符串拼接）返回一行说明。
    return None


def daily_status(minutes, goal):
    """达到或超过目标时返回“达标”，否则返回“未达标”。"""
    # TODO：用 if / else 判断 minutes 与 goal 的关系。
    return None


def weekly_summary(records, goal):
    """返回一份字典：total、average、goal_days。

    空列表时，三个值都应为 0。
    average 可以是整数或小数，但必须是 total / 记录条数。
    """
    # TODO：用 for 循环累计总量和达标天数，再计算平均值。
    return None


# 挑战任务：完成后取消下面函数的注释，并实现最长连续达标天数。
# def longest_goal_streak(records, goal):
#     return 0
