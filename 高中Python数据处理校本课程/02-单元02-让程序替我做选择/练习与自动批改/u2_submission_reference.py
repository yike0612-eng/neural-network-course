"""U2 自动批改参考提交文件。"""


def is_short_time(free_minutes):
    return free_minutes < 10


def basic_advice(free_minutes, task_done):
    if not task_done:
        return "完成任务"
    elif is_short_time(free_minutes):
        return "短时整理"
    return "自由安排"


def suggest_activity(weather, free_minutes, task_done):
    if not task_done:
        return "完成任务"
    elif is_short_time(free_minutes):
        return "短时整理"
    elif weather == "雨":
        return "室内活动"
    elif weather == "晴" and free_minutes >= 30:
        return "户外活动"
    return "自由安排"


def batch_advice(situations):
    suggestions = []
    for situation in situations:
        suggestion = suggest_activity(
            situation["weather"],
            situation["free_minutes"],
            situation["task_done"],
        )
        suggestions.append(suggestion)
    return suggestions


def count_indoor_advice(advice_list):
    indoor_count = 0
    for advice in advice_list:
        if advice == "室内活动":
            indoor_count += 1
    return indoor_count
