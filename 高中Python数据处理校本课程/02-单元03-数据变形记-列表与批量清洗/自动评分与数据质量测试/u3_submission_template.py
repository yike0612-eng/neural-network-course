"""U3 自动评分提交模板。
只修改 TODO 部分；不要修改函数名称和参数。
"""


def clean_minutes(raw_value):
    """返回 (clean_value, issue_reason)。"""
    # TODO 1：把输入转为文本并去除首尾空格。
    # TODO 2：按你在规则表中写明的约定处理“分钟”单位。
    # TODO 3：空白、无效文本和负数返回 (None, 原因)。
    # TODO 4：有效的非负整数返回 (整数, None)。
    return None, "尚未完成"


def transform_records(raw_records):
    """返回 (clean_records, issues)。"""
    clean_records = []
    issues = []

    for record in raw_records:
        # TODO：调用 clean_minutes(record["minutes"])
        # TODO：按 issue 是否为空，把记录放入不同列表。
        pass

    return clean_records, issues


def summarize_records(clean_records, issues):
    """可选：返回汇总字典，便于教师检查统计口径。"""
    # TODO：至少包含 valid_count、issue_count、total_minutes、average_minutes。
    return {}
