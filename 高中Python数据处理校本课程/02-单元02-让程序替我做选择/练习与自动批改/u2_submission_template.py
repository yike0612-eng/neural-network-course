"""U2 自动批改提交模板。

只保留函数定义；不要写 import、input、print、文件读写或顶层测试代码。
展示用程序请另存为 campus_task_helper.py。
"""


def is_short_time(free_minutes):
    """可支配时间少于 10 分钟时返回 True，否则返回 False。"""
    # TODO：写出一个比较表达式。
    return None


def basic_advice(free_minutes, task_done):
    """返回“完成任务”“短时整理”或“自由安排”。"""
    # TODO：先判断任务是否完成，再判断时间是否短。
    return None


def suggest_activity(weather, free_minutes, task_done):
    """按规定优先级返回五种建议之一。

    “完成任务”“短时整理”“室内活动”“户外活动”“自由安排”。
    """
    # TODO：使用 if / elif / else 完成多分支规则。
    return None


def batch_advice(situations):
    """对多条模拟情境逐条调用 suggest_activity，返回建议列表。"""
    # TODO：使用 for 循环，不要改变 situations 原列表。
    return None


# 挑战任务：完成后取消注释。
# def count_indoor_advice(advice_list):
#     return 0
